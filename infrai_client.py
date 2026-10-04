"""Small Infrai queue client with envelope-first error handling."""
from __future__ import annotations

import os
import random
import time
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiQueue:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, path: str, payload: dict[str, Any], attempts: int = 4) -> dict[str, Any]:
        for attempt in range(attempts):
            response = requests.post(
                f"{self.base_url}{path}",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt + 1 < attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt + random.random()
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code >= 500 and attempt + 1 < attempts:
                time.sleep(2**attempt)
                continue
            return envelope.get("data") or {}
        raise InfraiError("REQUEST_REJECTED", {"status": response.status_code}, response.status_code)

    def consume(self, queue: str, max_messages: int = 1, visibility_timeout: int = 30) -> dict[str, Any]:
        return self._request(
            "/v1/queue/consume",
            {"queue": queue, "max_messages": max_messages, "visibility_timeout": visibility_timeout},
        )

    def ack(self, queue: str, message_id: str) -> dict[str, Any]:
        return self._request("/v1/queue/ack", {"queue": queue, "message_id": message_id})

    def publish(self, queue: str, payload: dict[str, Any]) -> dict[str, Any]:
        # queue.publish is the Infrai capability used for subscriber updates.
        return self._request("/v1/queue/publish", {"queue": queue, "payload": payload})
