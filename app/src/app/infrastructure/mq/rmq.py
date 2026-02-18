from __future__ import annotations

import os
import time
import pika

def rabbit_url() -> str:
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = os.getenv("RABBITMQ_PORT", "5672")
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    return f"amqp://{user}:{password}@{host}:{port}/%2F"

def get_connection_with_retry(retries: int = 20, delay_sec: float = 1.0) -> pika.BlockingConnection:
    url = rabbit_url()
    last_exc = None
    for _ in range(retries):
        try:
            params = pika.URLParameters(url)
            return pika.BlockingConnection(params)
        except Exception as e:
            last_exc = e
            time.sleep(delay_sec)
    raise RuntimeError(f"RabbitMQ connection failed: {last_exc}")

def ensure_queue(channel: pika.adapters.blocking_connection.BlockingChannel, queue_name: str) -> None:
    channel.queue_declare(queue=queue_name, durable=True)