from __future__ import annotations

import json
import logging
import os
import socket
import time
from datetime import datetime, timezone
from uuid import UUID

import pika
from sqlalchemy import create_engine, text

from hf_model import HFTimeSeriesModel


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ml-worker")


RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", "5672"))
RABBIT_USER = os.getenv("RABBIT_USER", "guest")
RABBIT_PASS = os.getenv("RABBIT_PASS", "guest")
RABBIT_QUEUE = os.getenv("RABBIT_QUEUE", "ml_tasks")

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise RuntimeError("DB_URL is required for worker")

WORKER_ID = os.getenv("WORKER_ID") or socket.gethostname()


DDL = """
CREATE TABLE IF NOT EXISTS ml_task_results (
    task_id    text PRIMARY KEY,
    model      text NOT NULL,
    prediction jsonb,
    worker_id  text,
    status     text NOT NULL,
    error      text,
    created_at timestamptz NOT NULL
);
"""


UPSERT = """
INSERT INTO ml_task_results (task_id, model, prediction, worker_id, status, error, created_at)
VALUES (:task_id, :model, CAST(:prediction AS jsonb), :worker_id, :status, :error, :created_at)
ON CONFLICT (task_id) DO UPDATE SET
    prediction = EXCLUDED.prediction,
    worker_id  = EXCLUDED.worker_id,
    status     = EXCLUDED.status,
    error      = EXCLUDED.error,
    created_at = EXCLUDED.created_at;
"""


def init_db(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(DDL))


def save_result(engine, result: dict) -> None:
    payload = dict(result)
    pred = payload.get("prediction")
    payload["prediction"] = None if pred is None else json.dumps(pred)
    with engine.begin() as conn:
        conn.execute(text(UPSERT), payload)


def validate_message(payload: dict) -> tuple[str, str, list[float], int]:
    task_id = payload.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")
    UUID(str(task_id))

    model = payload.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model is required")

    features = payload.get("features")
    if not isinstance(features, dict):
        raise ValueError("features must be an object")

    series = features.get("series")
    horizon = features.get("horizon")
    if not isinstance(series, list) or len(series) == 0:
        raise ValueError("features.series must be a non-empty array")
    if not isinstance(horizon, int) or horizon <= 0:
        raise ValueError("features.horizon must be a positive integer")

    clean_series = [float(x) for x in series]
    return str(task_id), model, clean_series, horizon


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True, future=True)
    init_db(engine)

    model = HFTimeSeriesModel()
    logger.info("[%s] HF model ready", WORKER_ID)

    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(
        host=RABBIT_HOST,
        port=RABBIT_PORT,
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30,
    )

    while True:
        try:
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.queue_declare(queue=RABBIT_QUEUE, durable=True)
            ch.basic_qos(prefetch_count=1)

            logger.info("[%s] Connected to RabbitMQ, queue='%s'. Waiting...", WORKER_ID, RABBIT_QUEUE)

            def on_message(channel, method, properties, body: bytes):
                payload = {}
                try:
                    payload = json.loads(body.decode("utf-8"))
                    task_id, model_name, series, horizon = validate_message(payload)

                    prediction = model.predict(series, horizon)

                    result = {
                        "task_id": task_id,
                        "model": model_name,
                        "prediction": prediction,
                        "worker_id": WORKER_ID,
                        "status": "SUCCESS",
                        "error": None,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    save_result(engine, result)
                    logger.info("[%s] DONE task=%s", WORKER_ID, task_id)

                except Exception as e:
                    logger.exception("[%s] FAIL: %s", WORKER_ID, e)
                    task_id = None
                    try:
                        task_id = str(payload.get("task_id"))
                    except Exception:
                        task_id = "invalid-task"

                    result = {
                        "task_id": task_id,
                        "model": str((payload or {}).get("model") or "unknown"),
                        "prediction": None,
                        "worker_id": WORKER_ID,
                        "status": "FAILED",
                        "error": str(e),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    try:
                        save_result(engine, result)
                    except Exception:
                        logger.exception("[%s] FAIL saving result", WORKER_ID)
                finally:
                    channel.basic_ack(delivery_tag=method.delivery_tag)

            ch.basic_consume(queue=RABBIT_QUEUE, on_message_callback=on_message)
            ch.start_consuming()

        except Exception as e:
            logger.exception("[%s] RabbitMQ connection error, retry in 2s: %s", WORKER_ID, e)
            time.sleep(2)


if __name__ == "__main__":
    main()
