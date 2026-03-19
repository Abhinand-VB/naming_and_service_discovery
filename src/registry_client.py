from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from threading import Event, Thread
from typing import Any, Dict, List, Optional

import requests


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Instance:
    address: str
    uptime_seconds: Optional[float] = None


class RegistryClient:
    """
    Small client for our service registry.

    Responsibilities:
    - register / heartbeat / deregister for a specific instance
    - discover instances for a service
    """

    def __init__(
        self,
        registry_url: str,
        timeout_s: float = 3.0,
        user_agent: str = "naming-and-discovery/1.0",
    ) -> None:
        self.registry_url = registry_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept": "application/json"})

    def _url(self, path: str) -> str:
        return f"{self.registry_url}/{path.lstrip('/')}"

    def wait_until_ready(self, max_wait_s: float, retry_every_s: float = 0.5) -> bool:
        deadline = time.time() + max_wait_s
        while time.time() < deadline:
            try:
                r = self.session.get(self._url("/health"), timeout=self.timeout_s)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(retry_every_s)
        return False

    def register(self, service: str, address: str) -> None:
        r = self.session.post(
            self._url("/register"),
            json={"service": service, "address": address},
            timeout=self.timeout_s,
        )
        r.raise_for_status()

    def deregister(self, service: str, address: str) -> None:
        r = self.session.post(
            self._url("/deregister"),
            json={"service": service, "address": address},
            timeout=self.timeout_s,
        )
        if r.status_code in (200, 404):
            return
        r.raise_for_status()

    def heartbeat(self, service: str, address: str) -> None:
        r = self.session.post(
            self._url("/heartbeat"),
            json={"service": service, "address": address},
            timeout=self.timeout_s,
        )
        if r.status_code == 200:
            return
        # If registry restarted and lost state, heartbeat may 404; caller can re-register
        if r.status_code == 404:
            raise RuntimeError(f"heartbeat not found for {service} {address}: {r.text}")
        r.raise_for_status()

    def discover(self, service: str) -> List[Instance]:
        r = self.session.get(self._url(f"/discover/{service}"), timeout=self.timeout_s)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        data: Dict[str, Any] = r.json()
        out: List[Instance] = []
        for inst in data.get("instances", []):
            out.append(Instance(address=inst["address"], uptime_seconds=inst.get("uptime_seconds")))
        return out


class HeartbeatLoop:
    """
    Runs heartbeats in the background.
    If the registry forgets the instance (404), we re-register.
    """

    def __init__(
        self,
        client: RegistryClient,
        service: str,
        address: str,
        interval_s: float = 5.0,
    ) -> None:
        self.client = client
        self.service = service
        self.address = address
        self.interval_s = interval_s
        self._stop = Event()
        self._thread: Optional[Thread] = None

    def start(self) -> None:
        if self._thread is not None:
            return

        def _run() -> None:
            while not self._stop.is_set():
                try:
                    self.client.heartbeat(self.service, self.address)
                    logger.info("heartbeat ok service=%s address=%s", self.service, self.address)
                except Exception as e:
                    logger.warning("heartbeat failed; attempting re-register error=%r", e)
                    try:
                        self.client.register(self.service, self.address)
                        logger.info("re-registered service=%s address=%s", self.service, self.address)
                    except Exception as e2:
                        logger.error("re-register failed error=%r", e2)

                self._stop.wait(self.interval_s)

        self._thread = Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()


def env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v not in (None, "") else default

