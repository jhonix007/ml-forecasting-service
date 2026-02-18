from __future__ import annotations

import json
import logging
import os
import socket
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import pika
from pika.adapters.blocking_connection import BlockingChannel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.base import Base
from app.infrastructure.db.orm_models import MLTaskORM

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ml-worker")


def _get_env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value != "":
            return value
    return default


# Настройки брокера сообщений
RABBIT_HOST = _get_env("RABBIT_HOST", "RABBITMQ_HOST", default="rabbitmq")
RABBIT_PORT = int(_get_env("RABBIT_PORT", "RABBITMQ_PORT", default="5672"))
RABBIT_USER = _get_env("RABBIT_USER", "RABBITMQ_USER", default="guest")
RABBIT_PASS = _get_env("RABBIT_PASS", "RABBITMQ_PASSWORD", default="guest")
RABBIT_QUEUE = _get_env("RABBIT_QUEUE", "RABBITMQ_QUEUE", default="ml_tasks")

# Идентификатор воркера
WORKER_ID = os.getenv("WORKER_ID") or socket.gethostname()


def _build_db_url() -> str | None:
    db_url = _get_env("DB_URL", "DATABASE_URL")
    if db_url:
        return db_url

    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([host, port, name, user, password]):
        return None

    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


# БД (для записи результата). Если строка подключения не задана — будем просто логировать.
DB_URL = _build_db_url()  # пример: postgresql+psycopg2://postgres:postgres@database:5432/postgres


def _validate_task(payload: dict[str, Any]) -> tuple[str, dict[str, float], str]:
    """Минимальная валидация под требования задания."""
    task_id = payload.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")
    UUID(str(task_id))  # проверка UUID

    model = payload.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model is required and must be a non-empty string")

    features = payload.get("features")
    if not isinstance(features, dict) or not features:
        raise ValueError("features is required and must be a non-empty object")

    clean: dict[str, float] = {}
    for k, v in features.items():
        if not isinstance(k, str) or not k.strip():
            raise ValueError("feature keys must be non-empty strings")
        if not isinstance(v, (int, float)):
            raise ValueError(f"feature '{k}' must be numeric")
        clean[k] = float(v)

    return str(task_id), clean, model


def _predict_mock(features: dict[str, float]) -> float:
    """Mock-модель: сумма фич (детерминированно, удобно проверять)."""
    return float(sum(features.values()))


def _init_db(engine) -> None:
    Base.metadata.create_all(engine)


def _save_result_db(session_factory, result: dict[str, Any]) -> None:
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
        task.prediction = result.get("prediction")
        task.worker_id = result["worker_id"]
        task.status = result["status"]
        task.error = result.get("error")

        if task.created_at is None:
            task.created_at = result["created_at"]

        db.commit()


def _handle_message(body: bytes) -> dict[str, Any]:
    payload = json.loads(body.decode("utf-8"))
    task_id, features, model = _validate_task(payload)

    # делаем предикт
    y = _predict_mock(features)

    return {
        "task_id": task_id,
        "model": model,
        "prediction": y,
        "worker_id": WORKER_ID,
        "status": "SUCCESS",
        "error": None,
        "created_at": datetime.now(timezone.utc),
    }


def main() -> None:
    engine = None
    session_factory = None
    if DB_URL:
        engine = create_engine(DB_URL, pool_pre_ping=True)
        _init_db(engine)
        session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        logger.info("[%s] DB enabled", WORKER_ID)
    else:
        logger.warning("[%s] DB_URL not set -> results will NOT be persisted", WORKER_ID)

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
            ch: BlockingChannel = conn.channel()

            # очередь одна, устойчивая
            ch.queue_declare(queue=RABBIT_QUEUE, durable=True)

            # важно для распределения по кругу между воркерами: один воркер = одна задача за раз
            ch.basic_qos(prefetch_count=1)

            logger.info("[%s] Connected to RabbitMQ, queue='%s'. Waiting...", WORKER_ID, RABBIT_QUEUE)

            def on_message(channel: BlockingChannel, method, properties, body: bytes):
                try:
                    result = _handle_message(body)

                    logger.info("[%s] DONE task=%s pred=%s", WORKER_ID, result["task_id"], result["prediction"])

                    if session_factory is not None:
                        _save_result_db(session_factory, result)

                    channel.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    logger.exception("[%s] FAIL: %s", WORKER_ID, e)

                    if session_factory is not None:
                        try:
                            bad = json.loads(body.decode("utf-8"))
                            task_id = str(bad.get("task_id") or "invalid-task")
                        except Exception:
                            task_id = "invalid-task"

                        fail_result = {
                            "task_id": task_id,
                            "model": str((bad or {}).get("model") or "unknown"),
                            "prediction": None,
                            "worker_id": WORKER_ID,
                            "status": "FAILED",
                            "error": str(e)[:500],
                            "created_at": datetime.now(timezone.utc),
                        }
                        _save_result_db(session_factory, fail_result)

                    # чтобы не зациклиться на кривом сообщении — не возвращаем в очередь
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            ch.basic_consume(queue=RABBIT_QUEUE, on_message_callback=on_message)
            ch.start_consuming()

        except Exception as e:
            logger.exception("[%s] RabbitMQ connection error, retry in 2s: %s", WORKER_ID, e)
            time.sleep(2)


if __name__ == "__main__":
    main()
