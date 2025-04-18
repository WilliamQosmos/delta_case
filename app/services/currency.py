import httpx

from app.core.config import settings
from app.utils.redis import get_cache, set_cache

CURRENCY_CACHE_KEY = "currency:usd_to_rub"


async def get_usd_to_rub_rate() -> float:
    """
    Получает текущий курс доллара к рублю.
    Сначала проверяет кэш, если данных нет, делает запрос к API.
    
    Returns:
        float: Курс доллара к рублю
    """
    cached_rate = await get_cache(CURRENCY_CACHE_KEY)
    if cached_rate is not None:
        return float(cached_rate)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.CURRENCY_API_URL)
            response.raise_for_status()
            data = response.json()
            rate = data["Valute"]["USD"]["Value"]

            await set_cache(
                CURRENCY_CACHE_KEY,
                rate,
                ttl=settings.CURRENCY_CACHE_TTL
            )

            return float(rate)
    except Exception as e:
        # В случае ошибки возвращаем дефолтное значение курса
        # В реальном приложении здесь должно быть логирование ошибки
        return 75.0  # Примерное значение
