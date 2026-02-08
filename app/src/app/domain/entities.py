from datetime import datetime
from typing import Optional, List
from uuid import UUID

from app.core.time import now_utc
from app.domain.enums import Role, TransactionType, TaskStatus, ModelKind
from app.domain.errors import InsufficientBalanceError, UnauthorizedError
from app.domain.value_objects import Credits, CreditsCost, InvalidRow


class User:
    """Пользователь сервиса (Web/REST/TG)."""

    def __init__(
        self,
        user_id: UUID,
        email: str,
        password_hash: str,
        role: Role = Role.USER,
        created_at: Optional[datetime] = None,
        is_active: bool = True,
    ) -> None:
        self._id = user_id
        self._email = email
        self._password_hash = password_hash
        self._role = role
        self._created_at = created_at or now_utc()
        self._is_active = is_active

    def is_admin(self) -> bool:
        return self._role == Role.ADMIN


class Wallet:
    """Баланс в кредитах + правила списания/пополнения."""

    def __init__(self, user_id: UUID, balance: Credits) -> None:
        self._user_id = user_id
        self._balance = balance

    def top_up(self, amount: Credits) -> None:
        self._balance = Credits(self._balance.value + amount.value)

    def can_spend(self, cost: CreditsCost) -> bool:
        return self._balance.value >= cost.value

    def spend(self, cost: CreditsCost) -> None:
        if not self.can_spend(cost):
            raise InsufficientBalanceError("Not enough credits")
        self._balance = Credits(self._balance.value - cost.value)


class Transaction:
    """История пополнений/списаний (аудит)."""

    def __init__(
        self,
        tx_id: UUID,
        user_id: UUID,
        tx_type: TransactionType,
        amount: Credits,
        created_at: Optional[datetime] = None,
        related_task_id: Optional[UUID] = None,
        comment: str = "",
    ) -> None:
        self._id = tx_id
        self._user_id = user_id
        self._type = tx_type
        self._amount = amount
        self._created_at = created_at or now_utc()
        self._related_task_id = related_task_id
        self._comment = comment


class MLModel:
    """Каталог доступных ML-моделей (версии/включена ли модель)."""

    def __init__(
        self,
        model_id: UUID,
        name: str,
        kind: ModelKind,
        version: str,
        is_active: bool = True,
    ) -> None:
        self._id = model_id
        self._name = name
        self._kind = kind
        self._version = version
        self._is_active = is_active


class MLTask:
    """
    Асинхронная задача для воркеров (RabbitMQ).
    Создаётся API, выполняется воркером, меняет статус.
    """

    def __init__(
        self,
        task_id: UUID,
        user_id: UUID,
        model_id: UUID,
        horizon: int,
        payload_ref: str,
        cost: CreditsCost,
        status: TaskStatus = TaskStatus.PENDING,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> None:
        self._id = task_id
        self._user_id = user_id
        self._model_id = model_id
        self._horizon = horizon
        self._payload_ref = payload_ref
        self._cost = cost
        self._status = status
        self._created_at = created_at or now_utc()
        self._updated_at = updated_at or self._created_at
        self._error_message = error_message

    def mark_running(self) -> None:
        self._status = TaskStatus.RUNNING
        self._updated_at = now_utc()

    def mark_succeeded(self) -> None:
        self._status = TaskStatus.SUCCEEDED
        self._updated_at = now_utc()

    def mark_failed(self, error_message: str) -> None:
        self._status = TaskStatus.FAILED
        self._error_message = error_message
        self._updated_at = now_utc()


class Prediction:
    """История предсказаний: прогноз + ошибки входных данных + списанные кредиты."""

    def __init__(
        self,
        prediction_id: UUID,
        task_id: UUID,
        user_id: UUID,
        model_id: UUID,
        horizon: int,
        valid_count: int,
        invalid_rows: List[InvalidRow],
        forecast: List[float],
        credits_spent: CreditsCost,
        created_at: Optional[datetime] = None,
    ) -> None:
        self._id = prediction_id
        self._task_id = task_id
        self._user_id = user_id
        self._model_id = model_id
        self._horizon = horizon
        self._valid_count = valid_count
        self._invalid_rows = invalid_rows
        self._forecast = forecast
        self._credits_spent = credits_spent
        self._created_at = created_at or now_utc()


class Actor:
    """Авторизованный актор, выполняющий действия в системе."""
    def __init__(self, user: User) -> None:
        self._user = user


class AdminActor(Actor):
    """Актор с повышенными правами (опциональная часть)."""
    def ensure_admin(self) -> None:
        if not self._user.is_admin():
            raise UnauthorizedError("Admin privileges required")