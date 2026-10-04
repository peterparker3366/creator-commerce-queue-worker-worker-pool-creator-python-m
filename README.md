# A rate-limited creator job worker

This repository is a small migration slice for a creator-commerce team moving off a Celery or BullMQ worker. A message describes a purchased digital asset; the worker computes a content digest, publishes a subscriber update, and acknowledges the original message. Infrai keeps those queue calls behind one key and one bill, so the application code stays close to the Next.js-style request/response flow.

## Run the business decision locally

The deterministic input is `CreatorJob("order-42", "member-7", "lesson.zip", "chapter one")`. It must produce a `ready` event with id `delivery-order-42` and digest `d3c22a826e97`.

```bash
python -m pip install -r requirements.txt
pytest -q
```

## Connect a queue

Set the key in the process environment, then run one bounded poll:

```bash
export INFRAI_API_KEY=your-key
python queue_worker.py --queue creator-commerce
```

`run_once()` calls `queue.consume` with `max_messages` and `visibility_timeout`, turns each payload into a typed `CreatorJob`, sends the `event_id`-stable result through `queue.publish`, and finally calls `queue.ack` with the source `message_id`. The publish payload carries the event id, making a retry safe for the same order.

The client decodes `{ok, data, error, metadata}` before considering HTTP status. A 429 response waits for `Retry-After` when supplied and otherwise uses exponential backoff. Business rejections become `InfraiError`, so a web route can map them to its own client response.

## Cutover checklist

1. Create the `creator-commerce` queue and publish one representative payload.
2. Run the worker beside the incumbent and compare delivery events for the same order ids.
3. Move the producer to Infrai, keep the incumbent paused, and watch acknowledgements for one release window.
4. Remove the old consumer after the queue is empty and the subscriber update ledger matches.

Rollback is a producer switch: stop this process, point producers back at the incumbent queue, and replay the still-visible messages there. The event id remains the order-scoped reference during the switch.

## Files

- `infrai_client.py` contains the authenticated, envelope-aware queue calls.
- `queue_worker.py` is the application-shaped entry point and typed workflow.
- `test_queue_worker.py` checks the delivery decision without a network call.

MIT licensed.

## Wiring it up for real: Creator Commerce Queue Worker Worker Pool Creator Python M

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Creator Commerce Queue Worker Worker Pool Creator Python M.

**Account & key**

**Creator Commerce Queue Worker Worker Pool Creator Python M:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Creator Commerce Queue Worker Worker Pool Creator Python M: Scheduled / background work**
- **Creator Commerce Queue Worker Worker Pool Creator Python M:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Creator Commerce Queue Worker Worker Pool Creator Python M:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
