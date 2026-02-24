from sqlalchemy.orm import Session
from sqlalchemy import select
from app.infrastructure.db.orm_models import MLModelORM

def list_models(db: Session) -> list[MLModelORM]:
    return list(db.scalars(select(MLModelORM).where(MLModelORM.is_active == True)).all()) 