import json
from typing import Any

import redis.asyncio as redis
from redis.asyncio.client import Redis

from app.core.config import settings

redis_client: Redis = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)


async def get_redis_client() -> Redis:
    return redis_client


async def get_cache(key: str) -> Any | None:
    """
    Получает значение из кэша Redis по ключу.
    
    Args:
        key: Ключ кэша
        
    Returns:
        Any | None: Значение из кэша или None, если ключа нет
    """
    value = await redis_client.get(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return None


async def set_cache(key: str, value: Any, ttl: int | None = None) -> bool:
    """
    Устанавливает значение в кэш Redis.
    
    Args:
        key: Ключ кэша
        value: Значение для сохранения
        ttl: Время жизни в секундах
        
    Returns:
        bool: True если успешно, иначе False
    """
    try:
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value)
        if ttl:
            await redis_client.setex(key, ttl, value)
        else:
            await redis_client.set(key, value)
        return True
    except Exception:
        return False


async def delete_cache(key: str) -> bool:
    """
    Удаляет значение из кэша Redis по ключу.
    
    Args:
        key: Ключ кэша
        
    Returns:
        bool: True если успешно, иначе False
    """
    return await redis_client.delete(key) > 0
