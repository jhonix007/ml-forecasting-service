from __future__ import annotations

import json
import logging
import os
import socket
import time
from datetime import datetime, timezone
from uuid import UUID

import pika
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hf_model import HFTimeSeriesModel
from app.infrastructure.db.base import Base
from app.infrastructure.db.orm_models import MLTaskORM


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


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def save_result(session_factory, result: dict) -> None:
    with session_factory() as db:
        task = db.get(MLTaskORM, result["task_id"])
        if task is None:
            task = MLTaskORM(
                task_id=result["task_id"],
                model=result["model"],
                created_at=result["created_at"],
            )
            db.add(task)

        task.model = result["model"]
        task.prediction = result["prediction"]
        task.worker_id = result["worker_id"]
        task.status = result["status"]
        task.error = result["error"]

        if task.created_at is None:
            task.created_at = result["created_at"]

        db.commit()


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
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

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
                        "created_at": datetime.now(timezone.utc),
                    }
                    save_result(SessionLocal, result)
                    logger.info("[%s] DONE task=%s", WORKER_ID, task_id)

                except Exception as e:
                    logger.exception("[%s] FAIL: %s", WORKER_ID, e)
                    try:
                        task_id = str((payload or {}).get("task_id") or "invalid-task")
                    except Exception:
                        task_id = "invalid-task"

                    result = {
                        "task_id": task_id,
                        "model": str((payload or {}).get("model") or "unknown"),
                        "prediction": None,
                        "worker_id": WORKER_ID,
                        "status": "FAILED",
                        "error": str(e)[:500],
                        "created_at": datetime.now(timezone.utc),
                    }
                    try:
                        save_result(SessionLocal, result)
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
