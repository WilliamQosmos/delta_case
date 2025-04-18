from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.session import get_or_create_session
from app.db.session import get_db
from app.models.package import Package
from app.models.package_type import PackageType
from app.models.user_session import UserSession
from app.schemas.package import (
    Package as PackageSchema,
    PackageCreate,
    PackageFilter,
    PackageAssignCompany,
)
from app.schemas.response import Response, PaginatedResponse, PackageCreateResponse
from app.services.package import (
    get_package,
    get_packages,
    assign_shipping_company,
)
from app.utils.logging import app_logger as logger
from app.workers.package_processor import send_package_to_queue

router = APIRouter()


@router.post(
    "/",
    response_model=PackageCreateResponse,
    status_code=201
)
async def register_package(
        package_data: PackageCreate,
        db: AsyncSession = Depends(get_db),
        user_session: UserSession = Depends(get_or_create_session),
):
    """
    Регистрирует новую посылку и отправляет ее в очередь для расчета стоимости доставки.
    """
    logger.info(f"Registering new package: {package_data.name}")

    try:
        result = await db.execute(
            select(PackageType).where(PackageType.id == package_data.package_type_id)
        )
        package_type = result.scalars().first()

        if not package_type:
            logger.warning(f"Package type ID {package_data.package_type_id} not found")
            raise HTTPException(
                status_code=404,
                detail=f"Тип посылки с ID {package_data.package_type_id} не найден"
            )

        message_data = {
            "package_data": {
                "name": package_data.name,
                "weight": package_data.weight,
                "price_usd": package_data.price_usd,
                "package_type_id": package_data.package_type_id,
                "user_session_id": user_session.id
            }
        }

        success = await send_package_to_queue(message_data, routing_key="package.create")

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Ошибка при отправке данных в очередь обработки"
            )

        return PackageCreateResponse(
            success=True,
            message="Посылка успешно отправлена на обработку",
            data={"status": "processing"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering package: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при регистрации посылки")


@router.get(
    "/",
    response_model=PaginatedResponse[PackageSchema]
)
async def list_packages(
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
        package_type_id: int | None = Query(None, description="Фильтр по типу посылки"),
        has_shipping_cost: bool | None = Query(None, description="Фильтр по наличию рассчитанной стоимости доставки"),
        db: AsyncSession = Depends(get_db),
        user_session: UserSession = Depends(get_or_create_session),
):
    """
    Получает список посылок с пагинацией и фильтрацией.
    """
    logger.info(f"Listing packages for session {user_session.session_id}, page {page}, size {page_size}")

    try:
        # Создаем объект фильтра
        filters = None
        if package_type_id is not None or has_shipping_cost is not None:
            filters = PackageFilter(
                package_type_id=package_type_id,
                has_shipping_cost=has_shipping_cost
            )

        skip = (page - 1) * page_size

        packages, total = await get_packages(
            db=db,
            user_session=user_session,
            skip=skip,
            limit=page_size,
            filters=filters
        )

        total_pages = (total + page_size - 1) // page_size

        return PaginatedResponse(
            success=True,
            message="Список посылок успешно получен",
            data=[PackageSchema.model_validate(x) for x in packages],
            total=total,
            page=page,
            size=page_size,
            pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error listing packages: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении списка посылок")


@router.get(
    "/{package_id}",
    response_model=Response[PackageSchema]
)
async def get_package_by_id(
        package_id: int,
        db: AsyncSession = Depends(get_db),
        user_session: UserSession = Depends(get_or_create_session),
):
    """
    Получает данные о посылке по ее ID.
    """
    logger.info(f"Getting package with ID {package_id}")

    try:
        package = await get_package(db, package_id, user_session)

        if not package:
            logger.warning(f"Package with ID {package_id} not found for session {user_session.session_id}")
            raise HTTPException(status_code=404, detail="Посылка не найдена")

        return Response(
            success=True,
            message="Данные о посылке успешно получены",
            data=package
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving package {package_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при получении данных о посылке")


@router.post(
    "/{package_id}/assign-company",
    response_model=Response
)
async def assign_company_to_package(
        package_id: int,
        company_data: PackageAssignCompany,
        db: AsyncSession = Depends(get_db),
):
    """
    Привязывает посылку к транспортной компании.
    Учитывает конкуренцию за посылку между компаниями.
    """
    logger.info(f"Assigning company {company_data.shipping_company_id} to package {package_id}")

    try:
        result = await db.execute(
            select(Package).where(Package.id == package_id)
        )
        package = result.scalars().first()

        if not package:
            logger.warning(f"Package with ID {package_id} not found")
            raise HTTPException(status_code=404, detail="Посылка не найдена")

        success = await assign_shipping_company(
            db=db,
            package_id=package_id,
            shipping_company_id=company_data.shipping_company_id
        )

        if success:
            return Response(
                success=True,
                message="Посылка успешно привязана к транспортной компании"
            )
        else:
            result = await db.execute(
                select(Package).where(Package.id == package_id)
            )
            updated_package = result.scalars().first()

            if updated_package.shipping_company_id:
                logger.warning(
                    f"Package {package_id} already assigned to company {updated_package.shipping_company_id}"
                )
                raise HTTPException(
                    status_code=409,
                    detail=f"Посылка уже привязана к транспортной компании {updated_package.shipping_company_id}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Не удалось привязать посылку к транспортной компании"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning company to package {package_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка при привязке посылки к транспортной компании"
        )
