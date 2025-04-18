from fastapi import APIRouter

from app.api.endpoints import packages, package_types

api_router = APIRouter()

api_router.include_router(
    packages.router,
    prefix="/packages",
    tags=["packages"]
)
api_router.include_router(
    package_types.router,
    prefix="/package-types",
    tags=["package-types"]
)
