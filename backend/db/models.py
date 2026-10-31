"""
Krishi Mitra — SQLAlchemy 2.0 Database Models
Defines User, OTPCode, and RefreshToken models with timezone-aware datetime support.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Uuid, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db.database import Base


class TZDateTime(TypeDecorator):
    """
    Timezone-aware DateTime decorator that safely attaches timezone.utc
    for SQLite which stores datetimes naively.
    """
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phone: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, default=""
    )
    preferred_language: Mapped[str] = mapped_column(
        String(8), default="kn", nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(32), default="farmer", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime, default=utc_now, nullable=False
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "phone": self.phone,
            "name": self.name or "",
            "preferred_language": self.preferred_language,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phone: Mapped[str] = mapped_column(
        String(32), index=True, nullable=False
    )
    code_hash: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        TZDateTime, nullable=False
    )
    attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime, default=utc_now, nullable=False
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False, default=uuid.uuid4
    )
    device_info: Mapped[Optional[str]] = mapped_column(
        String(256), nullable=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        TZDateTime, nullable=True, default=None
    )
    expires_at: Mapped[datetime] = mapped_column(
        TZDateTime, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TZDateTime, default=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
