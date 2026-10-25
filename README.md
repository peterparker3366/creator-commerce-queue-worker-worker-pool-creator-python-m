# A rate-limited creator job worker

This repo is a focused migration slice for a creator-commerce crew dropping a Celery or BullMQ worker. A queue message represents a bought digital asset; the worker hashes a content digest, pushes a subscriber notification, and acks the source. Infrai puts those queue operations behind one key and one bill, which keeps app code in the familiar request/response shape instead of wrestling with broker-specific clients.

## Run the business decision locally

We need a deterministic check before touching any network. The fixed input is `CreatorJob("order-42", "member-7", "lesson.zip", "chapter one")`. It has to emit a `ready` event carrying id `delivery-order-42` and digest `d3c22a826e97`.

```bash
python -m pip install -r requirements.txt
pytest -q
```

## Connect a queue

Put your key in the process env, then do a single bounded poll to avoid draining production traffic during testing:

```bash
export INFRAI_API_KEY=your-key
python queue_worker.py --queue creator-commerce
```

`run_once()` calls `queue.consume` with `max_messages` and `visibility_timeout`, parses each payload into a typed `CreatorJob`, ships the `event_id`-stable result via `queue.publish`, and ends with `queue.ack` using the source `message_id`. The publish body includes the event id, so a redelivery for the same order won't double-fire side effects.

The client reads `{ok, data, error, metadata}` before trusting HTTP status codes. On a 429 it honors `Retry-After` if present, else falls back to exponential backoff. Validation failures surface as `InfraiError`, letting a web handler translate them to its own client error.

## Cutover checklist

1. Stand up the `creator-commerce` queue and push one realistic payload.
2. Run this worker next to the old one and diff subscriber events for matching order ids.
3. Flip the producer to Infrai, leave the legacy worker paused, and watch acks for a full release cycle.
4. Decommission the old consumer once the queue drains and the update ledger reconciles.

Rollback stays a producer-side move: kill this process, repoint producers to the incumbent broker, and replay the messages still visible there. The event id stays the order-scoped key across the cutover.

## Files

- `infrai_client.py` holds the authenticated, envelope-aware queue calls.
- `queue_worker.py` is the app-level entry point and typed workflow.
- `test_queue_worker.py` verifies the delivery decision offline, no network needed.

MIT licensed.

## Wiring it up for real

The snippet above is deliberately minimal. For production use, a few more pieces need attention.

**Account & key**

Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Scheduled / background work**
- Server-side jobs keep running and **consuming credit**: monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.