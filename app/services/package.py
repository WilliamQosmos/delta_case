from typing import Any, Sequence

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.package import Package
from app.models.user_session import UserSession
from app.schemas.package import PackageCreate, PackageFilter
from app.services.shipping_cost import calculate_shipping_cost


async def create_package(
        db: AsyncSession,
        obj_in: PackageCreate,
        user_session: UserSession
) -> Package:
    """
    Создает новую посылку в базе данных.
    
    Args:
        db: Сессия базы данных
        obj_in: Данные для создания посылки
        user_session: Объект сессии пользователя
        
    Returns:
        Package: Созданная посылка
    """
    db_obj = Package(
        name=obj_in.name,
        weight=obj_in.weight,
        price_usd=obj_in.price_usd,
        package_type_id=obj_in.package_type_id,
        user_session_id=user_session.id,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def get_package(
        db: AsyncSession,
        package_id: int,
        user_session: UserSession
) -> Package | None:
    """
    Получает посылку по ID для текущей сессии пользователя.
    
    Args:
        db: Сессия базы данных
        package_id: ID посылки
        user_session: Объект сессии пользователя
        
    Returns:
        Package | None: Найденная посылка или None
    """
    result = await db.execute(
        select(Package)
        .options(selectinload(Package.package_type))
        .where(
            Package.id == package_id,
            Package.user_session_id == user_session.id
        )
    )
    return result.scalars().first()


async def get_packages(
        db: AsyncSession,
        user_session: UserSession,
        skip: int = 0,
        limit: int = 100,
        filters: PackageFilter | None = None,
) -> tuple[Sequence[Package], Any | None]:
    """
    Получает список посылок с пагинацией и фильтрацией.
    
    Args:
        db: Сессия базы данных
        user_session: Объект сессии пользователя
        skip: Сколько записей пропустить
        limit: Сколько записей вернуть
        filters: Фильтры для выборки
        
    Returns:
        tuple[Sequence[Package], int]: Список посылок и общее количество записей
    """
    query = (
        select(
            Package,
        )
        .where(Package.user_session_id == user_session.id)
    )

    if filters:
        if filters.package_type_id is not None:
            query = query.where(Package.package_type_id == filters.package_type_id)
        if filters.has_shipping_cost is not None:
            query = query.where(Package.is_shipping_cost_calculated == filters.has_shipping_cost)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    result = await db.execute(
        query.offset(skip).limit(limit)
    )

    return result.scalars().all(), total


async def update_shipping_cost(
        db: AsyncSession,
        package_id: int,
        shipping_cost: float
) -> bool:
    """
    Обновляет стоимость доставки для посылки.
    
    Args:
        db: Сессия базы данных
        package_id: ID посылки
        shipping_cost: Рассчитанная стоимость доставки
        
    Returns:
        bool: True, если обновление успешно, иначе False
    """
    result = await db.execute(
        update(Package)
        .where(Package.id == package_id)
        .values(
            shipping_cost=shipping_cost,
            is_shipping_cost_calculated=True
        )
    )
    await db.commit()
    return result.rowcount > 0


async def assign_shipping_company(
        db: AsyncSession,
        package_id: int,
        shipping_company_id: int
) -> bool:
    """
    Привязывает посылку к транспортной компании.

    Args:
        db: Сессия базы данных
        package_id: ID посылки
        shipping_company_id: ID транспортной компании
        
    Returns:
        bool: True, если привязка успешна, иначе False
    """
    result = await db.execute(
        update(Package)
        .where(
            and_(
                Package.id == package_id,
                Package.shipping_company_id.is_(None)
            )
        )
        .values(shipping_company_id=shipping_company_id)
    )
    await db.commit()
    return result.rowcount > 0


async def calculate_and_update_shipping_cost(
        db: AsyncSession,
        package_id: int
) -> float | None:
    """
    Рассчитывает и обновляет стоимость доставки для посылки.
    
    Args:
        db: Сессия базы данных
        package_id: ID посылки
        
    Returns:
        float | None: Рассчитанная стоимость доставки или None в случае ошибки
    """
    result = await db.execute(
        select(Package).where(Package.id == package_id)
    )
    package = result.scalars().first()

    if not package:
        return None

    shipping_cost = await calculate_shipping_cost(
        weight=package.weight,
        price_usd=package.price_usd
    )

    await update_shipping_cost(db, package_id, shipping_cost)

    return shipping_cost
