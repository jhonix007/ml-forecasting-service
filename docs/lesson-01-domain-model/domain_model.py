from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol, Optional, List, Any
from uuid import UUID


# =============================================================================
# Контекст проекта
# -----------------------------------------------------------------------------
# Личный кабинет пользователя ML-сервиса прогнозирования временных рядов.
# Пользователь загружает ряд числовых значений (например, цена/спрос/метрика)
# и задаёт горизонт прогноза (horizon). Сервис возвращает прогноз на N шагов вперёд.
#
# Дополнительно реализуются:
# - баланс в кредитах, списание кредитов за успешный прогноз
# - история транзакций (пополнения/списания)
# - история предсказаний (входные данные, ошибки в данных, прогноз, стоимость)
#
# Выполнение прогнозов асинхронное:
# API создаёт MLTask и отправляет в очередь,
# воркеры валидируют данные, делают предикт и сохраняют Prediction.
# =============================================================================


def now_utc() -> datetime:
    """Единый способ получать текущее время (timezone-aware)."""
    return datetime.now(timezone.utc)


# =============================================================================
# Перечисления (Enums)
# -----------------------------------------------------------------------------
# Enum используется, чтобы ограничить набор допустимых значений
# и избежать "магических строк" и опечаток в бизнес-логике.
# =============================================================================

class Role(Enum):
    # Роль пользователя (обычный или админ)
    USER = "USER"
    ADMIN = "ADMIN"


class TransactionType(Enum):
    # Тип операции по балансу
    TOP_UP = "TOP_UP"   # пополнение
    CHARGE = "CHARGE"   # списание


class TaskStatus(Enum):
    # Статусы выполнения ML-задачи (асинхронная обработка)
    PENDING = "PENDING"       # создана и ждёт воркера
    RUNNING = "RUNNING"       # воркер взял в работу
    SUCCEEDED = "SUCCEEDED"   # выполнена успешно
    FAILED = "FAILED"         # выполнена с ошибкой


class ModelKind(Enum):
    # Тип ML-модели. Сейчас только прогноз временных рядов,
    # но в будущем можно добавить другие типы задач.
    TIMESERIES_FORECASTING = "TIMESERIES_FORECASTING"


# =============================================================================
# Value Objects (объекты-значения)
# -----------------------------------------------------------------------------
# Это маленькие "контейнеры смысла". Их удобно делать неизменяемыми (frozen=True),
# чтобы не было неожиданных изменений "по ссылке".
# =============================================================================

@dataclass(frozen=True)
class Credits:
    # Баланс пользователя в условных кредитах
    value: int

    def __post_init__(self) -> None:
        # Контроль бизнес-инварианта: баланс не может быть отрицательным
        if self.value < 0:
            raise ValueError("Credits.value must be >= 0")


@dataclass(frozen=True)
class CreditsCost:
    # Стоимость ML-запроса (сколько списывать кредитов при успехе)
    value: int

    def __post_init__(self) -> None:
        # Стоимость должна быть положительной
        if self.value <= 0:
            raise ValueError("CreditsCost.value must be > 0")


@dataclass(frozen=True)
class InvalidRow:
    # Описание "плохой" строки/значения во входной выборке
    index: int        # индекс элемента (например, позиция в списке или строка CSV)
    raw_value: Any    # исходное значение (строка/None/и т.п.)
    error: str        # почему это ошибка


@dataclass(frozen=True)
class ValidatedSeries:
    # Результат валидации:
    # values — валидные числа, которые можно передать в модель
    # invalid_rows — список ошибок, которые нужно вернуть пользователю
    values: List[float]
    invalid_rows: List[InvalidRow]


@dataclass(frozen=True)
class ForecastRequest:
    # Внутренний запрос к ML-движку прогнозирования
    model_id: UUID
    horizon: int         # сколько точек вперёд прогнозируем
    values: List[float]  # временной ряд (валидные числа)


@dataclass(frozen=True)
class ForecastResult:
    # Результат работы модели: прогноз
    forecast: List[float]


# =============================================================================
# Entities (сущности)
# -----------------------------------------------------------------------------
# Entity — это объект с "идентичностью" и жизненным циклом.
# Например: пользователь, кошелек, транзакция, задача, предикт.
# =============================================================================

class User:
    # Пользователь системы (для Web/REST/Telegram)
    def __init__(
        self,
        user_id: UUID,
        email: str,
        password_hash: str,
        role: Role = Role.USER,
        created_at: Optional[datetime] = None,
        is_active: bool = True,
    ) -> None:
        # Приватные поля (по соглашению Python: подчёркивание)
        self._id: UUID = user_id
        self._email: str = email
        self._password_hash: str = password_hash
        self._role: Role = role
        self._created_at: datetime = created_at or now_utc()
        self._is_active: bool = is_active

    # Публичный доступ на чтение через свойства
    @property
    def id(self) -> UUID:
        return self._id

    @property
    def email(self) -> str:
        return self._email

    @property
    def role(self) -> Role:
        return self._role

    # Методы поведения
    def verify_password(self, password_hash: str) -> bool:
        # В реальном проекте сравнение делается по хэшу пароля
        return self._password_hash == password_hash

    def deactivate(self) -> None:
        self._is_active = False

    def is_admin(self) -> bool:
        return self._role == Role.ADMIN


class InsufficientBalanceError(Exception):
    # Ошибка: не хватает кредитов на операцию
    pass


class Wallet:
    # Кошелек пользователя: хранит баланс и контролирует пополнение/списание
    def __init__(self, user_id: UUID, balance: Credits) -> None:
        self._user_id: UUID = user_id
        self._balance: Credits = balance

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def balance(self) -> Credits:
        return self._balance

    def top_up(self, amount: Credits) -> None:
        # Увеличиваем баланс: создаём новый Credits (так как Credits frozen)
        self._balance = Credits(self._balance.value + amount.value)

    def can_spend(self, cost: CreditsCost) -> bool:
        return self._balance.value >= cost.value

    def spend(self, cost: CreditsCost) -> None:
        # Списание разрешаем только если кредитов достаточно
        if not self.can_spend(cost):
            raise InsufficientBalanceError("Not enough credits")
        self._balance = Credits(self._balance.value - cost.value)


class Transaction:
    # Запись в истории операций по балансу (аудит)
    def __init__(
        self,
        tx_id: UUID,
        user_id: UUID,
        tx_type: TransactionType,
        amount: Credits,  # сколько пополнили/списали
        created_at: Optional[datetime] = None,
        related_task_id: Optional[UUID] = None,  # если списание связано с MLTask
        comment: str = "",
    ) -> None:
        self._id: UUID = tx_id
        self._user_id: UUID = user_id
        self._type: TransactionType = tx_type
        self._amount: Credits = amount
        self._created_at: datetime = created_at or now_utc()
        self._related_task_id: Optional[UUID] = related_task_id
        self._comment: str = comment

    @property
    def user_id(self) -> UUID:
        return self._user_id

    @property
    def type(self) -> TransactionType:
        return self._type

    @property
    def amount(self) -> Credits:
        return self._amount

    @property
    def created_at(self) -> datetime:
        return self._created_at


class MLModel:
    # Реестр доступных моделей в сервисе (например TimesFM, baseline и т.п.)
    def __init__(
        self,
        model_id: UUID,
        name: str,
        kind: ModelKind,
        version: str,
        is_active: bool = True,
    ) -> None:
        self._id: UUID = model_id
        self._name: str = name
        self._kind: ModelKind = kind
        self._version: str = version
        self._is_active: bool = is_active

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def deactivate(self) -> None:
        # Отключаем модель от использования, но не удаляем из истории
        self._is_active = False


class MLTask:
    # Задача на выполнение ML (асинхронно через очередь)
    def __init__(
        self,
        task_id: UUID,
        user_id: UUID,
        model_id: UUID,
        horizon: int,
        payload_ref: str,          # ссылка на загруженные данные (файл/объект)
        cost: CreditsCost,         # стоимость, которую нужно списать при успехе
        status: TaskStatus = TaskStatus.PENDING,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> None:
        self._id: UUID = task_id
        self._user_id: UUID = user_id
        self._model_id: UUID = model_id
        self._horizon: int = horizon
        self._payload_ref: str = payload_ref
        self._cost: CreditsCost = cost
        self._status: TaskStatus = status
        self._created_at: datetime = created_at or now_utc()
        self._updated_at: datetime = updated_at or self._created_at
        self._error_message: Optional[str] = error_message

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def cost(self) -> CreditsCost:
        return self._cost

    # Методы смены статуса: их будет вызывать воркер
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
    # Результат выполнения MLTask (то, что показываем в "истории предсказаний")
    def __init__(
        self,
        prediction_id: UUID,
        task_id: UUID,
        user_id: UUID,
        model_id: UUID,
        horizon: int,
        valid_count: int,                 # сколько точек реально пошло в модель
        invalid_rows: List[InvalidRow],   # какие элементы были некорректны
        forecast: List[float],            # сам прогноз
        credits_spent: CreditsCost,       # сколько списали кредитов
        created_at: Optional[datetime] = None,
    ) -> None:
        self._id: UUID = prediction_id
        self._task_id: UUID = task_id
        self._user_id: UUID = user_id
        self._model_id: UUID = model_id
        self._horizon: int = horizon
        self._valid_count: int = valid_count
        self._invalid_rows: List[InvalidRow] = invalid_rows
        self._forecast: List[float] = forecast
        self._credits_spent: CreditsCost = credits_spent
        self._created_at: datetime = created_at or now_utc()


# =============================================================================
# Контракты и реализации: валидация и прогнозирование
# -----------------------------------------------------------------------------
# Здесь показано, что можно подменять валидатор и "движок" модели,
# не переписывая бизнес-логику сервиса.
# =============================================================================

class IDataValidator(Protocol):
    # Любой валидатор должен уметь:
    # принять сырые значения (из CSV/JSON) и вернуть валидные + список ошибок
    def validate_series(self, raw_values: List[Any]) -> ValidatedSeries:
        ...


class BasicNumericValidator:
    # Простая валидация для MVP:
    # - преобразуем каждое значение в float
    # - NaN/Inf считаем ошибкой
    # - ошибки накапливаем для показа пользователю
    def validate_series(self, raw_values: List[Any]) -> ValidatedSeries:
        values: List[float] = []
        invalid: List[InvalidRow] = []

        for i, v in enumerate(raw_values):
            try:
                fv = float(v)
                # fv != fv — проверка на NaN
                if fv != fv or fv in (float("inf"), float("-inf")):
                    raise ValueError("NaN/Inf not allowed")
                values.append(fv)
            except Exception as e:
                invalid.append(InvalidRow(index=i, raw_value=v, error=str(e)))

        return ValidatedSeries(values=values, invalid_rows=invalid)


class IForecastingEngine(Protocol):
    # Любой движок прогнозирования должен уметь принять ForecastRequest
    # и вернуть ForecastResult
    def forecast(self, req: ForecastRequest) -> ForecastResult:
        ...


class BaselineForecastEngine:
    # Простейшая "модель": повторяем последнее значение N раз
    # Полезно как baseline и для тестов/отладки системы
    def forecast(self, req: ForecastRequest) -> ForecastResult:
        last = req.values[-1]
        return ForecastResult(forecast=[last] * req.horizon)


# =============================================================================
# Роли: актор и администратор (опциональная часть задания)
# -----------------------------------------------------------------------------
# В AdminActor можно складывать операции, доступные только администратору:
# модерация пополнений, просмотр всех транзакций и т.п.
# =============================================================================

class UnauthorizedError(Exception):
    pass


class Actor:
    # "Actor" — пользователь, который выполняет действия в системе (после авторизации)
    def __init__(self, user: User) -> None:
        self._user = user

    @property
    def user(self) -> User:
        return self._user


class AdminActor(Actor):
    # Проверка прав: если роль не ADMIN — запрещаем выполнение админских операций
    def ensure_admin(self) -> None:
        if not self._user.is_admin():
            raise UnauthorizedError("Admin privileges required")
