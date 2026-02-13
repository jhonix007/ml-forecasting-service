"""
session.py
----------
Подключение к базе данных и создание SQLAlchemy Session.

Здесь мы:
1) собираем DATABASE_URL из env-переменных (app/.env)
2) создаём engine (соединение с PostgreSQL)
3) создаём SessionLocal — фабрику сессий для работы с БД

Важно:
- engine "тяжёлый" объект — создаётся один раз на процесс
- Session создаётся "на запрос"/"на сценарий" и потом закрывается
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _build_database_url() -> str:
    """
    Собираем строку подключения к PostgreSQL из переменных окружения.

    В docker-compose сервис Postgres называется 'database',
    поэтому в контейнере app DB_HOST обычно = 'database'.
    """
    host = os.getenv("DB_HOST", "database")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "app_db")
    user = os.getenv("DB_USER", "app_user")
    password = os.getenv("DB_PASSWORD", "app_pass")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = _build_database_url()

# pool_pre_ping=True — полезно для докера: проверяет соединение перед запросом
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# autoflush=False — не отправляем изменения в БД автоматически
# autocommit=False — транзакции контролируем сами (commit/rollback)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
