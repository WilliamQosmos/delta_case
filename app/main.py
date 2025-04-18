from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import api_router
from app.core.config import settings
from app.utils.logging import setup_logging, app_logger as logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting Delivery Service API")

    # worker_process = multiprocessing.Process(target=start_worker)
    # worker_process.start()
    # logger.info(f"Started package processor worker (PID: {worker_process.pid})")
    yield
    # if worker_process.is_alive():
    #     worker_process.terminate()
    #     worker_process.join()
    #     logger.info("Stopped package processor worker")
    #
    logger.info("Delivery Service API stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie=settings.SESSION_COOKIE_NAME,
    max_age=settings.SESSION_COOKIE_MAX_AGE,
)


@app.middleware("http")
async def add_response_to_request(request: Request, call_next):
    response = Response()
    request.scope["fastapi_response"] = response
    return await call_next(request)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
