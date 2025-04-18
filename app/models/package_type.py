from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PackageType(Base):
    __tablename__ = "package_types"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    packages: Mapped[list["Package"]] = relationship(
        "Package", back_populates="package_type", lazy="selectin"
    )
