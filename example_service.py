"""
Example Service - Demonstrates how to register with the service registry

This simulates a microservice that:
1. Registers itself on startup
2. Sends periodic heartbeats
3. Deregisters on shutdown
"""

from __future__ import annotations

import os
import random
import socket
import requests
import time
import signal
import sys
from threading import Thread, Event
from typing import Optional

from flask import Flask, jsonify

class ServiceClient:
    def __init__(self, service_name, service_address, registry_url="http://localhost:5001"):
        self.service_name = service_name
        self.service_address = service_address
        self.registry_url = registry_url
        self.stop_event = Event()
        self.heartbeat_interval = 10  # seconds
        
    def register(self):
        """Register this service with the registry"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                f"{self.registry_url}/register",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                },
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                print(f"[OK] Registered {self.service_name} at {self.service_address}")
                return True
            else:
                print(f"[ERR] Registration failed (status {response.status_code})")
                print(f"   Response: {response.text if response.text else 'Empty response'}")
                print(f"   URL: {self.registry_url}/register")
                return False
        except requests.exceptions.ConnectionError:
            print(f"[ERR] Cannot connect to registry at {self.registry_url}")
            print(f"   Make sure the registry is running: python3 service_registry_improved.py")
            return False
        except requests.exceptions.Timeout:
            print(f"[ERR] Connection timeout to registry at {self.registry_url}")
            return False
        except Exception as e:
            print(f"[ERR] Registration error: {e}")
            return False
    
    def deregister(self):
        """Deregister this service from the registry"""
        try:
            response = requests.post(
                f"{self.registry_url}/deregister",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                }
            )
            
            if response.status_code == 200:
                print(f"[OK] Deregistered {self.service_name}")
                return True
            else:
                print(f"[ERR] Deregistration failed: {response.json()}")
                return False
        except Exception as e:
            print(f"[ERR] Deregistration error: {e}")
            return False
    
    def send_heartbeat(self):
        """Send heartbeat to registry"""
        try:
            response = requests.post(
                f"{self.registry_url}/heartbeat",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                }
            )
            
            if response.status_code == 200:
                print(f"[OK] Heartbeat sent for {self.service_name}")
                return True
            else:
                print(f"[ERR] Heartbeat failed: {response.json()}")
                return False
        except Exception as e:
            print(f"[ERR] Heartbeat error: {e}")
            return False
    
    def heartbeat_loop(self):
        """Background thread that sends periodic heartbeats"""
        while not self.stop_event.is_set():
            self.send_heartbeat()
            self.stop_event.wait(self.heartbeat_interval)
    
    def discover_service(self, service_name):
        """Discover instances of another service"""
        try:
            response = requests.get(f"{self.registry_url}/discover/{service_name}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n[DISCOVER] {service_name}:")
                print(f"   Found {data['count']} instance(s)")
                for instance in data['instances']:
                    print(f"   - {instance['address']} (uptime: {instance['uptime_seconds']:.1f}s)")
                return data['instances']
            else:
                print(f"[ERR] Discovery failed: {response.json()}")
                return []
        except Exception as e:
            print(f"[ERR] Discovery error: {e}")
            return []
    
    def start(self):
        """Start the service and register with registry"""
        # Register
        if not self.register():
            print("Failed to register. Exiting.")
            return
        
        # Start heartbeat thread
        heartbeat_thread = Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        print(f"\n{self.service_name} is running...")
        print("Press Ctrl+C to stop\n")
        
        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n\nShutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Keep the main thread alive
        while not self.stop_event.is_set():
            time.sleep(1)
    
    def stop(self):
        """Stop the service and deregister"""
        self.stop_event.set()
        self.deregister()


def _safe_join_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def _make_app(service_name: str, instance_id: str):
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": service_name, "instance_id": instance_id})

    @app.get("/whoami")
    def whoami():
        return jsonify({"service": service_name, "instance_id": instance_id})

    return app


def run_service(service_name: str, host: str, port: int, registry_url: str, advertised_base_url: str):
    instance_id = os.getenv("INSTANCE_ID") or f"{socket.gethostname()}-{port}"

    client = ServiceClient(
        service_name=service_name,
        service_address=_safe_join_url(advertised_base_url, ""),
        registry_url=registry_url,
    )

    if not client.register():
        print("Failed to register. Exiting.")
        return 1

    heartbeat_thread = Thread(target=client.heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    app = _make_app(service_name=service_name, instance_id=instance_id)
    server_thread = Thread(target=lambda: app.run(host=host, port=port, debug=False, use_reloader=False), daemon=True)
    server_thread.start()

    print(f"\n{service_name} is running.")
    print(f" - Listening on: http://{host}:{port}")
    print(f" - Advertising:  {advertised_base_url}")
    print(f" - Registry:     {registry_url}")
    print("Press Ctrl+C to stop\n")

    def signal_handler(sig, frame):
        print("\n\nShutting down gracefully...")
        client.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    while not client.stop_event.is_set():
        time.sleep(1)

    return 0


def run_client(target_service: str, registry_url: str, times: int, path: str = "/whoami"):
    print("\n" + "=" * 60)
    print("CLIENT DISCOVERY + RANDOM CALL DEMO")
    print("=" * 60)
    print(f"Registry: {registry_url}")
    print(f"Target:   {target_service}")
    print(f"Calls:    {times}\n")

    # Check registry health
    try:
        response = requests.get(_safe_join_url(registry_url, "/health"), timeout=5)
        response.raise_for_status()
        print("[OK] Registry is healthy\n")
    except Exception as e:
        print(f"[ERR] Cannot connect to registry: {e}")
        return 1

    client = ServiceClient(service_name="client", service_address="http://localhost", registry_url=registry_url)

    for i in range(1, times + 1):
        instances = client.discover_service(target_service)
        if not instances:
            print(f"No instances of {target_service} available.")
            return 2

        chosen = random.choice(instances)
        url = _safe_join_url(chosen["address"], path)
        try:
            r = requests.get(url, timeout=3)
            print(f"[{i}/{times}] Called {url} -> {r.status_code} {r.text.strip()}")
        except Exception as e:
            print(f"[{i}/{times}] Call failed to {url}: {e}")

        time.sleep(0.5)

    return 0


if __name__ == "__main__":
    # Env overrides (handy for Kubernetes)
    default_registry_url = os.getenv("REGISTRY_URL", "http://localhost:5001")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python example_service.py service <service_name> <port> [--host 0.0.0.0] [--advertise http://host:port]")
        print("  python example_service.py client <service_name> [--times 10] [--registry http://localhost:5001]")
        print("\nExamples:")
        print("  python example_service.py service user-service 8001 --advertise http://localhost:8001")
        print("  python example_service.py service user-service 8002 --advertise http://localhost:8002")
        print("  python example_service.py client user-service --times 10")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "service":
        if len(sys.argv) < 4:
            print("Usage: python example_service.py service <service_name> <port> [--host 0.0.0.0] [--advertise http://host:port] [--registry ...]")
            sys.exit(1)

        service_name = sys.argv[2]
        port = int(sys.argv[3])

        host = "0.0.0.0"
        advertise: Optional[str] = None
        registry_url = default_registry_url

        i = 4
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
                i += 2
            elif arg == "--advertise" and i + 1 < len(sys.argv):
                advertise = sys.argv[i + 1]
                i += 2
            elif arg == "--registry" and i + 1 < len(sys.argv):
                registry_url = sys.argv[i + 1]
                i += 2
            else:
                print(f"Unknown arg: {arg}")
                sys.exit(1)

        if advertise is None:
            advertise = f"http://localhost:{port}"

        sys.exit(run_service(service_name=service_name, host=host, port=port, registry_url=registry_url, advertised_base_url=advertise))

    if mode == "client":
        if len(sys.argv) < 3:
            print("Usage: python example_service.py client <service_name> [--times 10] [--registry ...]")
            sys.exit(1)

        target = sys.argv[2]
        times = 10
        registry_url = default_registry_url

        i = 3
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--times" and i + 1 < len(sys.argv):
                times = int(sys.argv[i + 1])
                i += 2
            elif arg == "--registry" and i + 1 < len(sys.argv):
                registry_url = sys.argv[i + 1]
                i += 2
            else:
                print(f"Unknown arg: {arg}")
                sys.exit(1)

        sys.exit(run_client(target_service=target, registry_url=registry_url, times=times))

    print(f"Unknown mode: {mode}")
    sys.exit(1)

# Made with Bob
