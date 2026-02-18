from __future__ import annotations

import json
import os
from datetime import datetime, timezone
import pika

from app.infrastructure.mq.rmq import get_connection_with_retry, ensure_queue

def publish_task(task: dict) -> None:
    queue = os.getenv("RABBITMQ_QUEUE", "ml_tasks")
    conn = get_connection_with_retry()
    try:
        ch = conn.channel()
        ensure_queue(ch, queue)

        body = json.dumps(task, ensure_ascii=False).encode("utf-8")
        ch.basic_publish(
            exchange="",
            routing_key=queue,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type="application/json",
                timestamp=int(datetime.now(timezone.utc).timestamp()),
            ),
        )
    finally:
        conn.close()