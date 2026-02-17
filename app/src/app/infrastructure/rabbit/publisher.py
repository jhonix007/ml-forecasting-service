from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pika


def _rabbit_settings() -> tuple[str, int, str, str, str]:
    host = os.getenv("RABBIT_HOST", "rabbitmq")
    port = int(os.getenv("RABBIT_PORT", "5672"))
    user = os.getenv("RABBIT_USER", "guest")
    password = os.getenv("RABBIT_PASS", "guest")
    queue = os.getenv("RABBIT_QUEUE", "ml_tasks")
    return host, port, user, password, queue


def publish_task(task: dict) -> None:
    host, port, user, password, queue = _rabbit_settings()

    credentials = pika.PlainCredentials(user, password)
    params = pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30,
    )

    conn = pika.BlockingConnection(params)
    try:
        ch = conn.channel()
        ch.queue_declare(queue=queue, durable=True)

        body = json.dumps(task, ensure_ascii=False).encode("utf-8")
        ch.basic_publish(
            exchange="",
            routing_key=queue,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                timestamp=int(datetime.now(timezone.utc).timestamp()),
            ),
        )
    finally:
        conn.close()
