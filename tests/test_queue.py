import pytest

from reference.queue import InMemoryQueueAdapter


def test_publish_receive_ack():
    queue = InMemoryQueueAdapter()
    message = queue.publish("job-1", {"value": 1})

    received = queue.receive()
    assert received.job_id == "job-1"
    assert received.payload == {"value": 1}

    queue.acknowledge(received)
    assert queue.is_acknowledged(message.delivery_id)


def test_reject_requeues_message():
    queue = InMemoryQueueAdapter()
    queue.publish("job-1", {"value": 1})

    first = queue.receive()
    queue.reject(first, requeue=True)
    second = queue.receive()

    assert second.job_id == first.job_id
    assert second.delivery_id != first.delivery_id


def test_empty_queue_times_out():
    queue = InMemoryQueueAdapter()
    with pytest.raises(TimeoutError):
        queue.receive()
