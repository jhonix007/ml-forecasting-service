from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from email_validator import validate_email, EmailNotValidError


class RegisterIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    # ВАЖНО: bcrypt лимит 72 bytes => ставим max_length <= 72 (по символам)
    password: str = Field(min_length=6, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_email_relaxed(cls, v: str) -> str:
        try:
            return validate_email(v, check_deliverability=False).email
        except EmailNotValidError as e:
            raise ValueError(str(e)) from e


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def validate_email_relaxed(cls, v: str) -> str:
        try:
            return validate_email(v, check_deliverability=False).email
        except EmailNotValidError as e:
            raise ValueError(str(e)) from e


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"