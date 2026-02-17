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
from sqlalchemy import create_engine, text

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
    """Создаём таблицу под результаты (самый простой способ выполнить 'записать результат')."""
    ddl = """
    CREATE TABLE IF NOT EXISTS ml_task_results (
        task_id      uuid PRIMARY KEY,
        model        text NOT NULL,
        features     jsonb NOT NULL,
        prediction   double precision,
        worker_id    text NOT NULL,
        status       text NOT NULL,
        error        text,
        created_at   timestamptz NOT NULL
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def _save_result_db(engine, result: dict[str, Any]) -> None:
    q = """
    INSERT INTO ml_task_results (task_id, model, features, prediction, worker_id, status, error, created_at)
    VALUES (CAST(:task_id AS uuid), :model, CAST(:features AS jsonb), :prediction, :worker_id, :status, :error, :created_at)
    ON CONFLICT (task_id) DO UPDATE SET
        prediction = EXCLUDED.prediction,
        worker_id  = EXCLUDED.worker_id,
        status     = EXCLUDED.status,
        error      = EXCLUDED.error,
        created_at = EXCLUDED.created_at;
    """
    params = {
        "task_id": result["task_id"],
        "model": result["model"],
        "features": json.dumps(result["features"], ensure_ascii=False),
        "prediction": result.get("prediction"),
        "worker_id": result["worker_id"],
        "status": result["status"],
        "error": result.get("error"),
        "created_at": result["created_at"],
    }
    with engine.begin() as conn:
        conn.execute(text(q), params)


def _handle_message(engine, body: bytes) -> dict[str, Any]:
    payload = json.loads(body.decode("utf-8"))
    task_id, features, model = _validate_task(payload)

    # делаем предикт
    y = _predict_mock(features)

    return {
        "task_id": task_id,
        "model": model,
        "features": features,
        "prediction": y,
        "worker_id": WORKER_ID,
        "status": "success",
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    engine = None
    if DB_URL:
        engine = create_engine(DB_URL, pool_pre_ping=True)
        _init_db(engine)
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
                    result = _handle_message(engine, body)

                    logger.info("[%s] DONE task=%s pred=%s", WORKER_ID, result["task_id"], result["prediction"])

                    if engine is not None:
                        _save_result_db(engine, result)

                    channel.basic_ack(delivery_tag=method.delivery_tag)

                except Exception as e:
                    logger.exception("[%s] FAIL: %s", WORKER_ID, e)

                    # сохраняем ошибку в БД (если есть)
                    if engine is not None:
                        try:
                            bad = json.loads(body.decode("utf-8"))
                            task_id = str(bad.get("task_id") or "00000000-0000-0000-0000-000000000000")
                        except Exception:
                            task_id = "00000000-0000-0000-0000-000000000000"

                        fail_result = {
                            "task_id": task_id,
                            "model": str((bad or {}).get("model") or "unknown"),
                            "features": (bad or {}).get("features") or {},
                            "prediction": None,
                            "worker_id": WORKER_ID,
                            "status": "failed",
                            "error": str(e),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                        _save_result_db(engine, fail_result)

                    # чтобы не зациклиться на кривом сообщении — не возвращаем в очередь
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            ch.basic_consume(queue=RABBIT_QUEUE, on_message_callback=on_message)
            ch.start_consuming()

        except Exception as e:
            logger.exception("[%s] RabbitMQ connection error, retry in 2s: %s", WORKER_ID, e)
            time.sleep(2)


if __name__ == "__main__":
    main()
