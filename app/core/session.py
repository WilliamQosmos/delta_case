import uuid
from datetime import datetime, timezone

from fastapi import Depends, Cookie, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.session import get_db
from app.models.user_session import UserSession


async def get_or_create_session(
        request: Request,
        session_id: str | None = Cookie(None, alias=settings.SESSION_COOKIE_NAME),
        db: AsyncSession = Depends(get_db),
) -> UserSession:
    """
    Получает существующую сессию пользователя или создает новую.
    
    Args:
        request: Запрос FastAPI
        session_id: ID сессии из cookie
        db: Сессия базы данных
        
    Returns:
        UserSession: Объект сессии пользователя
    """
    if session_id:
        result = await db.execute(
            select(UserSession).where(UserSession.session_id == session_id)
        )
        session = result.scalars().first()

        if session:
            session.last_activity = datetime.now(timezone.utc)
            db.add(session)
            await db.commit()
            await db.refresh(session)
            return session

    new_session_id = str(uuid.uuid4())
    new_session = UserSession(session_id=new_session_id)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    response = request.scope.get("fastapi_response")
    if response:
        response.set_cookie(
            settings.SESSION_COOKIE_NAME,
            new_session_id,
            max_age=settings.SESSION_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax"
        )

    return new_session
