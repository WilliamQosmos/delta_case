from typing import Any, TypeVar, Generic

from pydantic import BaseModel, Field, ConfigDict

DataT = TypeVar('DataT')


class ResponseBase(BaseModel):
    success: bool = True
    message: str = "Success"


class Response(ResponseBase, Generic[DataT]):
    data: DataT | None = None


class ErrorResponse(ResponseBase):
    success: bool = False
    message: str
    error_code: str | None = None
    details: dict[str, Any] | None = None


class PaginatedResponse(ResponseBase, Generic[DataT]):
    data: list[DataT]
    total: int
    page: int
    size: int
    pages: int


class PackageCreateResponse(ResponseBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Посылка успешно зарегистрирована",
                "data": {
                    "package_id": 1
                }
            }
        }
    )
    data: dict[str, Any] = Field(...)
