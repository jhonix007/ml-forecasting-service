"""
seed.py
-------
Инициализация БД начальными данными (seed).

Требования задания:
- демо пользователь
- демо администратор
- базовые ML модели

Важно:
seed должен быть идемпотентным — повторный запуск не ломает данные,
а просто "проверяет наличие" и добавляет недостающее.
"""

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.infrastructure.db.orm_models import UserORM, WalletORM, MLModelORM


def seed_data(db: Session) -> None:
    # --- demo user
    demo_email = "demo@local"
    user = db.scalar(select(UserORM).where(UserORM.email == demo_email))
    if not user:
        user = UserORM(email=demo_email, password_hash="demo_hash", role="USER")
        user.wallet = WalletORM(balance=1000)  # стартовый баланс демо пользователя
        db.add(user)

    # --- demo admin
    admin_email = "admin@local"
    admin = db.scalar(select(UserORM).where(UserORM.email == admin_email))
    if not admin:
        admin = UserORM(email=admin_email, password_hash="admin_hash", role="ADMIN")
        admin.wallet = WalletORM(balance=5000)
        db.add(admin)

    # --- базовые ML модели
    base_models = [
        ("BaselineForecastEngine", "0.1"),
        ("TimesFM", "2.0"),
    ]

    for name, version in base_models:
        existing = db.scalar(
            select(MLModelORM).where(
                MLModelORM.name == name,
                MLModelORM.version == version,
            )
        )
        if not existing:
            db.add(
                MLModelORM(
                    name=name,
                    version=version,
                    kind="TIMESERIES_FORECASTING",
                    is_active=True,
                )
            )

    db.commit()