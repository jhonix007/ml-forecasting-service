from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_session
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse

# Используем CRUD-функции:
# - create_user(session, email, password_hash)
# - get_user_by_email(session, email)
from app.services.crud.users import get_user_by_email, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> dict:
    existing = get_user_by_email(session, payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    # УЧЕБНО: храним password как есть нельзя, но JWT позже.
    # Сейчас можно сделать примитивный hash
    user = create_user(session, email=payload.email, password=payload.password)
    return {"id": str(user.id), "email": user.email}


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> AuthResponse:
    user = get_user_by_email(session, payload.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Подстройка под реализацию:
    if not user.verify_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return AuthResponse(token=f"user:{user.id}")
