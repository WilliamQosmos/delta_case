from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.package_type import PackageType
from app.schemas.package_type import PackageType as PackageTypeSchema
from app.schemas.response import Response
from app.utils.logging import app_logger as logger

router = APIRouter()


@router.get("/", response_model=Response[list[PackageTypeSchema]])
async def get_package_types(
        db: AsyncSession = Depends(get_db),
):
    """
    Получает список всех типов посылок.
    """
    logger.info("Request for all package types")

    try:
        result = await db.execute(select(PackageType))
        package_types = result.scalars().all()

        return Response(
            success=True,
            message="Типы посылок успешно получены",
            data=[
                PackageTypeSchema.model_validate(pt) for pt in package_types
            ]
        )
    except Exception as e:
        logger.error(f"Error retrieving package types: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении типов посылок")


@router.get("/{package_type_id}", response_model=Response[PackageTypeSchema])
async def get_package_type(
        package_type_id: int,
        db: AsyncSession = Depends(get_db),
):
    """
    Получает информацию о конкретном типе посылки по ID.
    """
    logger.info(f"Request for package type ID: {package_type_id}")

    try:
        result = await db.execute(
            select(PackageType).where(PackageType.id == package_type_id)
        )
        package_type = result.scalars().first()

        if not package_type:
            logger.warning(f"Package type ID {package_type_id} not found")
            raise HTTPException(status_code=404, detail="Тип посылки не найден")

        return Response(
            success=True,
            message="Тип посылки успешно получен",
            data=PackageTypeSchema.model_validate(package_type)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving package type {package_type_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении типа посылки")
