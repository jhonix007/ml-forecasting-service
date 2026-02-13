from sqlalchemy.orm import Session

from app.infrastructure.db.session import SessionLocal
from app.services.crud.users import create_user, get_user_by_email
from app.services.crud.wallet import top_up, charge
from app.services.crud.transactions import get_user_transactions
from app.services.crud.ml_models import list_models

def run() -> None:
    db: Session = SessionLocal()
    try:
        email = "test@local"
        user = get_user_by_email(db, email)
        if not user:
            user = create_user(db, email=email, password_hash="test_hash")

        print("USER:", user.id, user.email, user.role)

        balance = top_up(db, user.id, 200, comment="demo top up")
        print("BALANCE after top_up:", balance)

        balance = charge(db, user.id, 50, comment="demo charge")
        print("BALANCE after charge:", balance)

        txs = get_user_transactions(db, user.id, limit=10)
        print("TRANSACTIONS:")
        for t in txs:
            print(" -", t.tx_type, t.amount, t.comment, t.created_at)

        models = list_models(db)
        print("ML MODELS:")
        for m in models:
            print(" -", m.name, m.version)

    finally:
        db.close()

if __name__ == "__main__":
    run()