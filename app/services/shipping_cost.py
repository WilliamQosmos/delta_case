from app.services.currency import get_usd_to_rub_rate


async def calculate_shipping_cost(weight: float, price_usd: float) -> float:
    """
    Рассчитывает стоимость доставки по формуле:
    Стоимость = (вес в кг * 0.5 + стоимость содержимого в долларах * 0.01) * курс доллара к рублю
    
    Args:
        weight: Вес посылки в кг
        price_usd: Стоимость содержимого в долларах
        
    Returns:
        float: Рассчитанная стоимость доставки в рублях
    """
    usd_to_rub_rate = await get_usd_to_rub_rate()

    shipping_cost = (weight * 0.5 + price_usd * 0.01) * usd_to_rub_rate

    return round(shipping_cost, 2)


def get_shipping_cost_display(shipping_cost=None) -> str:
    """
    Возвращает отформатированную строку со стоимостью доставки.
    
    Args:
        shipping_cost: Стоимость доставки в рублях
        
    Returns:
        str: Строка со стоимостью доставки или "Не рассчитано"
    """
    if shipping_cost is None:
        return "Не рассчитано"
    return f"{shipping_cost:.2f} руб."
