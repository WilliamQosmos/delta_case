import asyncio
import json

import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.base import async_session
from app.models.user_session import UserSession
from app.schemas.package import PackageCreate
from app.services.package import calculate_and_update_shipping_cost, create_package
from app.utils.logging import app_logger as logger


class PackageProcessor:
    """
    Класс для обработки сообщений о регистрации посылок из RabbitMQ.
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def connect(self) -> None:
        """
        Устанавливает соединение с RabbitMQ.
        """
        try:
            rabbitmq_url = (
                f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
                f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/{settings.RABBITMQ_VHOST}"
            )

            logger.info(f"Connecting to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")

            self.connection = await aio_pika.connect_robust(rabbitmq_url)
            self.channel = await self.connection.channel()

            self.exchange = await self.channel.declare_exchange(
                "package_exchange",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            self.calculate_queue = await self.channel.declare_queue(
                "package_calculate_queue",
                durable=True
            )
            self.create_queue = await self.channel.declare_queue(
                "package_create_queue",
                durable=True
            )

            await self.calculate_queue.bind(self.exchange, routing_key="package.calculate")
            await self.create_queue.bind(self.exchange, routing_key="package.create")

            logger.info("Successfully connected to RabbitMQ")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def process_message(self, message: AbstractIncomingMessage) -> None:
        """
        Обрабатывает входящее сообщение с данными о посылке.
        
        Args:
            message: Входящее сообщение из RabbitMQ
        """
        async with message.process():
            try:
                body = message.body.decode()
                data = json.loads(body)

                routing_key = message.routing_key

                if routing_key == "package.calculate":
                    await self._process_calculate_message(data)
                elif routing_key == "package.create":
                    await self._process_create_message(data)
                else:
                    logger.warning(f"Unknown routing key: {routing_key}")

            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")

    async def _process_calculate_message(self, data: dict) -> None:
        """
        Обрабатывает сообщение для расчета стоимости доставки.
        
        Args:
            data: Данные сообщения
        """
        package_id = data.get("package_id")
        if not package_id:
            logger.error(f"Invalid message format - missing package_id: {data}")
            return

        logger.info(f"Processing package with ID: {package_id}")

        async with self.session_maker() as session:
            shipping_cost = await calculate_and_update_shipping_cost(
                db=session,
                package_id=package_id
            )

            if shipping_cost is not None:
                logger.info(f"Package {package_id}: calculated shipping cost {shipping_cost:.2f}")
            else:
                logger.error(f"Package {package_id}: failed to calculate shipping cost")

    async def _process_create_message(self, data: dict) -> None:
        """
        Обрабатывает сообщение для создания новой посылки.
        
        Args:
            data: Данные сообщения
        """
        package_data = data.get("package_data")
        if not package_data:
            logger.error(f"Invalid message format - missing package_data: {data}")
            return

        logger.info(f"Creating new package: {package_data.get('name')}")

        try:
            async with self.session_maker() as session:
                user_session_id = package_data.get("user_session_id")
                result = await session.execute(
                    select(UserSession).where(UserSession.id == user_session_id)
                )
                user_session = result.scalars().first()

                if not user_session:
                    raise Exception(f"User session with ID {user_session_id} not found")

                package_in = PackageCreate(
                    name=package_data.get("name"),
                    weight=package_data.get("weight"),
                    price_usd=package_data.get("price_usd"),
                    package_type_id=package_data.get("package_type_id")
                )

                package = await create_package(
                    db=session,
                    obj_in=package_in,
                    user_session=user_session
                )

                await send_package_to_queue(
                    {"package_id": package.id},
                    routing_key="package.calculate"
                )

                logger.info(f"Package created with ID: {package.id} and sent for cost calculation")

        except Exception as e:
            logger.error(f"Error creating package: {str(e)}")

    async def start_consuming(self) -> None:
        """
        Начинает потребление сообщений из очередей.
        """
        await self.connect()

        logger.info("Starting to consume messages from package queues")

        await self.calculate_queue.consume(self.process_message)
        await self.create_queue.consume(self.process_message)

    async def close(self) -> None:
        """
        Закрывает соединение с RabbitMQ.
        """
        if self.connection:
            await self.connection.close()
            logger.info("Closed connection to RabbitMQ")


# Функция для отправки сообщения в очередь RabbitMQ
async def send_package_to_queue(data: dict, routing_key: str = "package.calculate") -> bool:
    """
    Отправляет сообщение в очередь RabbitMQ.
    
    Args:
        data: Данные для отправки
        routing_key: Ключ маршрутизации
        
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    try:
        rabbitmq_url = (
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
            f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/{settings.RABBITMQ_VHOST}"
        )

        connection = await aio_pika.connect_robust(rabbitmq_url)

        async with connection:
            channel = await connection.channel()

            exchange = await channel.declare_exchange(
                "package_exchange",
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )

            message_body = json.dumps(data).encode()
            message = aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            await exchange.publish(
                message,
                routing_key=routing_key
            )

            logger.info(f"Sent message with routing key {routing_key} to RabbitMQ")
            return True

    except Exception as e:
        logger.error(f"Failed to send message to queue: {str(e)}")
        return False


async def run_worker() -> None:
    """
    Запускает воркер для обработки посылок.
    """
    worker = PackageProcessor(async_session)

    try:
        await worker.start_consuming()

        await asyncio.Future()

    except asyncio.CancelledError:
        logger.info("Worker shutdown initiated")
    except Exception as e:
        logger.error(f"Worker error: {str(e)}")
    finally:
        await worker.close()


def start_worker():
    """
    Запускает воркер в отдельном процессе.
    """
    asyncio.run(run_worker())
