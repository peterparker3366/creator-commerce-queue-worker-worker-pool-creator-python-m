"""Creator-commerce worker: process an asset and notify its subscriber."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from typing import Any

from infrai_client import InfraiQueue


@dataclass(frozen=True)
class CreatorJob:
    job_id: str
    subscriber_id: str
    asset_name: str
    content: str


def process_job(job: CreatorJob) -> dict[str, Any]:
    """Return the delivery event that should be published for a valid job."""
    digest = hashlib.sha256(job.content.encode("utf-8")).hexdigest()[:12]
    return {
        "event_id": f"delivery-{job.job_id}",
        "job_id": job.job_id,
        "subscriber_id": job.subscriber_id,
        "asset_name": job.asset_name,
        "content_digest": digest,
        "status": "ready",
    }


def _messages(data: dict[str, Any]) -> list[dict[str, Any]]:
    values = data.get("messages")
    return values if isinstance(values, list) else []


def run_once(client: InfraiQueue, queue_name: str) -> list[dict[str, Any]]:
    data = client.consume(queue_name, max_messages=10, visibility_timeout=60)
    results = []
    for message in _messages(data):
        payload = message.get("payload") or {}
        job = CreatorJob(
            job_id=str(payload["job_id"]),
            subscriber_id=str(payload["subscriber_id"]),
            asset_name=str(payload["asset_name"]),
            content=str(payload["content"]),
        )
        event = process_job(job)
        client.publish(queue_name, event)
        client.ack(queue_name, str(message["message_id"]))
        results.append(event)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Consume creator jobs from an Infrai queue")
    parser.add_argument("--queue", default="creator-commerce")
    args = parser.parse_args()
    events = run_once(InfraiQueue(), args.queue)
    print(json.dumps({"processed": len(events), "events": events}, indent=2))


if __name__ == "__main__":
    main()
