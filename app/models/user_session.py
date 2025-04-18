from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    packages: Mapped[list["Package"]] = relationship(
        "Package", back_populates="user_session", lazy="selectin"
    )
