from __future__ import annotations

import argparse
import logging
import os
import random
import time
from typing import Optional

import requests

from src.registry_client import RegistryClient, env


def main() -> int:
    parser = argparse.ArgumentParser(description="Client-side discovery + random instance caller")
    parser.add_argument("--registry-url", default=env("REGISTRY_URL", "http://localhost:5001"))
    parser.add_argument("--service-name", default=env("TARGET_SERVICE", "user-service"))
    parser.add_argument("--calls", type=int, default=int(env("CALLS", "10")))
    parser.add_argument("--path", default=env("CALL_PATH", "/info"))
    parser.add_argument("--sleep-ms", type=int, default=int(env("SLEEP_MS", "300")))
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logger = logging.getLogger("client")

    registry = RegistryClient(args.registry_url)
    if not registry.wait_until_ready(max_wait_s=10):
        logger.error("registry not reachable at %s", args.registry_url)
        return 2

    logger.info("discovering service=%s via registry=%s", args.service_name, args.registry_url)

    for i in range(1, args.calls + 1):
        instances = registry.discover(args.service_name)
        if not instances:
            logger.error("no instances found for service=%s", args.service_name)
            return 3

        chosen = random.choice(instances)  # REQUIRED: random selection each call
        url = chosen.address.rstrip("/") + "/" + args.path.lstrip("/")

        logger.info("call %d/%d -> chosen_instance=%s", i, args.calls, chosen.address)
        try:
            r = requests.get(url, timeout=3)
            logger.info("response status=%s body=%s", r.status_code, r.text.strip())
        except Exception as e:
            logger.error("request failed url=%s error=%r", url, e)

        time.sleep(max(args.sleep_ms, 0) / 1000.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

