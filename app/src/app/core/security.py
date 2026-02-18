from __future__ import annotations

# Backward compatibility layer.
# Реальная реализация перенесена в app.auth.*
from app.auth.hash_password import hash_password, verify_password
from app.auth.jwt_handler import (
    JWT_ALG,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET,
    create_access_token,
    decode_token,
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_token",
    "JWT_SECRET",
    "JWT_ALG",
    "JWT_EXPIRE_MINUTES",
]
