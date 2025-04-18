# Микросервис для Службы международной доставки

API для регистрации посылок и расчета стоимости их доставки.

## Функциональность

- Регистрация посылок с их типом, весом и стоимостью
- Расчет стоимости доставки по заданной формуле
- Получение списка типов посылок
- Получение списка своих посылок с пагинацией и фильтрацией
- Получение данных о конкретной посылке
- Привязка посылки к транспортной компании

## Технический стек

- FastAPI для API
- SQLAlchemy 2.0 для работы с базой данных (MySQL)
- Redis для кеширования курсов валют
- RabbitMQ для асинхронной обработки посылок
- Docker для контейнеризации

## Запуск проекта

### Предварительные требования

- Docker и docker-compose

### Шаги для запуска

1. Клонируйте репозиторий:

```
git clone <repository-url>
```

2. Создайте файл .env с переменными окружения:

```
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_DATABASE=delivery_service

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
```

3. Запустите приложение с помощью docker-compose:

```
docker-compose up -d --build
```

4. API будет доступно по адресу: http://localhost:8000

## API Endpoints

API документация доступна по адресу: http://localhost:8000/docs

### Основные эндпоинты:

- `POST /api/v1/packages/` - Зарегистрировать посылку
- `GET /api/v1/packages/` - Получить список своих посылок
- `GET /api/v1/packages/{package_id}` - Получить данные о посылке
- `POST /api/v1/packages/{package_id}/assign-company` - Привязать посылку к транспортной компании
- `GET /api/v1/package-types/` - Получить список типов посылок
- `GET /api/v1/package-types/{package_type_id}` - Получить данные о типе посылок

