from queue_worker import CreatorJob, process_job


def test_process_job_emits_repeatable_delivery_event():
    job = CreatorJob("order-42", "member-7", "lesson.zip", "chapter one")
    assert process_job(job) == {
        "event_id": "delivery-order-42",
        "job_id": "order-42",
        "subscriber_id": "member-7",
        "asset_name": "lesson.zip",
        "content_digest": "d3c22a826e97",
        "status": "ready",
    }
