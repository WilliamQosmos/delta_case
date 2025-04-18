from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, ConfigDict, AliasPath, BeforeValidator

from app.services.shipping_cost import get_shipping_cost_display


class PackageBase(BaseModel):
    name: str
    weight: float = Field(..., gt=0)
    price_usd: float = Field(..., ge=0)
    package_type_id: int


class PackageCreate(PackageBase):
    pass


class PackageUpdate(BaseModel):
    name: str | None = None
    weight: float | None = None
    price_usd: float | None = None
    package_type_id: int | None = None

    @field_validator('weight')
    def weight_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Вес должен быть положительным числом')
        return v

    @field_validator('price_usd')
    def price_must_be_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('Стоимость не может быть отрицательной')
        return v


class PackageAssignCompany(BaseModel):
    shipping_company_id: int = Field(..., gt=0)


class PackageInDB(PackageBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_session_id: int
    shipping_cost: float | None = None
    shipping_company_id: int | None = None
    is_shipping_cost_calculated: bool
    created_at: datetime
    updated_at: datetime


class Package(PackageBase):
    model_config = ConfigDict(from_attributes=True)
    shipping_cost: float | None = None
    is_shipping_cost_calculated: bool
    package_type_name: str = Field(validation_alias=AliasPath("package_type", "name"))
    shipping_cost_display: Annotated[str, BeforeValidator(get_shipping_cost_display)] = Field(
        validation_alias="shipping_cost")


class PackageFilter(BaseModel):
    package_type_id: int | None = None
    has_shipping_cost: bool | None = None
