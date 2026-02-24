"""
base.py
-------
Базовый класс SQLAlchemy для всех ORM-моделей.

SQLAlchemy требует общий "Base", от которого наследуются классы таблиц.
Поэтому Base потом можно создать все таблицы через:
Base.metadata.create_all(engine)
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Общий базовый класс для ORM-моделей."""
    pass