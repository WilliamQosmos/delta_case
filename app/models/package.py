from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)

    package_type_id: Mapped[int] = mapped_column(ForeignKey("package_types.id"), nullable=False)
    user_session_id: Mapped[int] = mapped_column(ForeignKey("user_sessions.id"), nullable=False)

    shipping_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    shipping_company_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_shipping_cost_calculated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )

    package_type: Mapped["PackageType"] = relationship("PackageType", back_populates="packages", lazy="selectin")
    user_session: Mapped["UserSession"] = relationship("UserSession", back_populates="packages")
