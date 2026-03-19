from __future__ import annotations

import argparse
import logging
import os
import socket
from typing import Dict

from flask import Flask, jsonify, request

from src.registry_client import HeartbeatLoop, RegistryClient, env


def build_app(service_name: str, instance_id: str, listen_host: str, listen_port: int) -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/info")
    def info():
        return jsonify(
            {
                "service": service_name,
                "instance_id": instance_id,
                "host": listen_host,
                "port": listen_port,
            }
        )

    @app.get("/echo")
    def echo():
        payload: Dict[str, str] = {"message": request.args.get("msg", "hello")}
        return jsonify(payload)

    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="User Service (registers to registry, runs HTTP)")
    parser.add_argument("--service-name", default=env("SERVICE_NAME", "user-service"))
    parser.add_argument("--host", default=env("SERVICE_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(env("SERVICE_PORT", "8001")))
    parser.add_argument("--registry-url", default=env("REGISTRY_URL", "http://localhost:5001"))
    parser.add_argument(
        "--advertise",
        default=env("ADVERTISE_URL", ""),
        help="Base URL to register in the registry (e.g. http://localhost:8001).",
    )
    parser.add_argument("--registry-wait-seconds", type=float, default=float(env("REGISTRY_WAIT_SECONDS", "15")))
    parser.add_argument("--heartbeat-interval-seconds", type=float, default=float(env("HEARTBEAT_INTERVAL_SECONDS", "5")))
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger = logging.getLogger("user_service")

    instance_id = os.getenv("INSTANCE_ID") or f"{socket.gethostname()}-{args.port}"
    advertise = args.advertise.strip() or f"http://{socket.gethostname()}:{args.port}"

    registry = RegistryClient(registry_url=args.registry_url)
    logger.info("starting service=%s instance_id=%s", args.service_name, instance_id)
    logger.info("listening_on=http://%s:%s advertise=%s", args.host, args.port, advertise)
    logger.info("registry_url=%s", args.registry_url)

    if not registry.wait_until_ready(max_wait_s=args.registry_wait_seconds):
        logger.error("registry not ready after %.1fs; exiting", args.registry_wait_seconds)
        return 2

    # Register with retries (registry might be up but slow)
    try:
        registry.register(args.service_name, advertise)
        logger.info("registered service=%s address=%s", args.service_name, advertise)
    except Exception as e:
        logger.exception("registration failed error=%r", e)
        return 3

    heartbeat = HeartbeatLoop(
        client=registry,
        service=args.service_name,
        address=advertise,
        interval_s=args.heartbeat_interval_seconds,
    )
    heartbeat.start()

    app = build_app(args.service_name, instance_id, args.host, args.port)

    try:
        app.run(host=args.host, port=args.port, debug=False, use_reloader=False)
    finally:
        heartbeat.stop()
        try:
            registry.deregister(args.service_name, advertise)
            logger.info("deregistered service=%s address=%s", args.service_name, advertise)
        except Exception as e:
            logger.warning("deregister failed error=%r", e)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

