"""
orm_models.py
-------------
ORM-модели (таблицы) проекта.

Цель проекта: личный кабинет пользователя ML-сервиса.
Пользователь имеет баланс в "кредитах" и может:
- пополнять баланс
- списывать кредиты за запросы
- смотреть историю транзакций
- использовать каталог доступных ML-моделей
- хранить историю предсказаний (минимальная версия)

Минимальные таблицы по заданию:
- users
- ml_models
- история ML-запросов/предсказаний (predictions)

Дополнительно для требований по балансу:
- wallets (баланс)
- transactions (история пополнений/списаний)
"""

from datetime import datetime
from uuid import uuid4


from sqlalchemy import (
    String,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    Float,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import now_utc
from app.infrastructure.db.base import Base


class UserORM(Base):
    """
    Таблица пользователей.

    email уникальный — по нему можно логиниться.
    role хранится строкой (USER / ADMIN) — для MVP это нормально.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)

    # 1:1 — у пользователя есть один кошелёк
    wallet: Mapped["WalletORM"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # 1-к-многим — история транзакций
    transactions: Mapped[list["TransactionORM"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class WalletORM(Base):
    """
    Таблица балансов.

    На MVP достаточно хранить один int balance (кредиты).
    Связь 1:1 — ключ user_id одновременно PK и FK на users.id.
    """

    __tablename__ = "wallets"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["UserORM"] = relationship(back_populates="wallet")


class TransactionORM(Base):
    """
    Таблица транзакций (история пополнений/списаний).

    tx_type:
      - TOP_UP  (пополнение)
      - CHARGE  (списание)
    amount — целое число кредитов (в рамках MVP).
    """

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    tx_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)

    user: Mapped["UserORM"] = relationship(back_populates="transactions")


class MLModelORM(Base):
    """
    Каталог доступных ML-моделей.

    Уникальность задаём парой (name, version), чтобы можно было хранить версии моделей.
    kind оставляем строкой, на MVP достаточно "TIMESERIES_FORECASTING".
    """

    __tablename__ = "ml_models"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_mlmodel_name_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, default="TIMESERIES_FORECASTING")
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)


class PredictionORM(Base):
    """
    История предсказаний / ML-запросов (упрощённая).

    На уроке 03 можно хранить только метаданные:
    - кто запросил (user_id)
    - какой моделью (model_id)
    - горизонт (horizon)
    - сколько валидных значений было
    - сколько кредитов списали

    Позже можно добавить:
    - сохранение результата forecast (JSON)
    - invalid_rows (JSON)
    - связь с MLTask
    """

    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ml_models.id"), nullable=False)

    horizon: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    credits_spent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)


class MLTaskORM(Base):
    """
    Результаты асинхронных ML-задач (RabbitMQ workers).

    Используется уроком 05: app кладёт PENDING, воркеры пишут SUCCESS/FAILED.
    """

    __tablename__ = "ml_task_results"

    task_id: Mapped[str] = mapped_column(String, primary_key=True)  # task_id (uuid string)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    model: Mapped[str] = mapped_column(String, nullable=False)
    prediction: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)  # jsonb в Postgres
    worker_id: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="PENDING")  # PENDING/SUCCESS/FAILED
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
