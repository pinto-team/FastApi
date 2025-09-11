from contextlib import asynccontextmanager
from uuid import uuid4
import logging
from logging.config import dictConfig

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.routes.product_routes import router as products_router
from app.routes.category_routes import router as categories_router
from app.routes.brand_routes import router as brands_router
from app.routes.upload_routes import router as upload_router
from app.models.response import make_error_response, make_success_response, ErrorDetail
from app.services.category_service import category_service


# -------------------------------
# Logging config (clean & scoped)
# -------------------------------
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s | %(name)s | %(message)s",
            "use_colors": True,
        },
        "app": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(asctime)s | %(name)s | %(message)s",
            "use_colors": True,
        },
    },

    "handlers": {
        "default": {  # for all other loggers
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
            "level": "INFO",
        },
        "app_handler": {  # verbose for our app.*
            "class": "logging.StreamHandler",
            "formatter": "app",
            "stream": "ext://sys.stdout",
            "level": "DEBUG",
        },
    },

    "loggers": {
        # root: keep it quieter (no spammy DEBUG from libs)
        "": {"handlers": ["default"], "level": "INFO"},

        # uvicorn
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"level": "WARNING"},

        # our app
        "app": {"handlers": ["app_handler"], "level": "DEBUG", "propagate": False},
        "app.main": {"handlers": ["app_handler"], "level": "DEBUG", "propagate": False},
        "app.routes": {"handlers": ["app_handler"], "level": "DEBUG", "propagate": False},
        "app.services": {"handlers": ["app_handler"], "level": "DEBUG", "propagate": False},

        # silence noisy libs
        "pymongo": {"level": "WARNING"},
        "motor": {"level": "WARNING"},
        "asyncio": {"level": "WARNING"},
        "httpx": {"level": "WARNING"},
        "urllib3": {"level": "WARNING"},
    },
}
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app.main")


# -------------------------------
# FastAPI settings
# -------------------------------
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await category_service.ensure_indexes()
        logger.info("✅ category indexes ensured successfully.")
    except Exception as e:
        logger.exception("❌ Failed to ensure indexes for categories: %s", e)
    yield
    # shutdown tasks if needed


app = FastAPI(
    title=settings.project_name,
    description="🛒 Mock API server for frontend testing until backend is ready",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# -------------------------------
# Middleware & Routes
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.include_router(upload_router, prefix="/files", tags=["Upload"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(categories_router, prefix="/categories", tags=["Categories"])
app.include_router(brands_router, prefix="/brands", tags=["Brands"])


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    request.state.correlation_id = correlation_id
    request.state.trace_id = str(uuid4())
    request.state.request_id = str(uuid4())

    response = await call_next(request)

    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Trace-ID"] = request.state.trace_id
    response.headers["X-Request-ID"] = request.state.request_id
    return response


# -------------------------------
# Exception Handlers
# -------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        field_path = ".".join(
            [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")]
        )
        details.append(
            ErrorDetail(field=field_path or None, message=err.get("msg", "Invalid input"))
        )
    body = make_error_response(request, code=422, message="validation.error", errors=details)
    return JSONResponse(status_code=422, content=body.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        body = make_error_response(request, code=exc.status_code, message=str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    logger.exception("Unhandled exception: %s", exc)
    body = make_error_response(request, code=500, message="internal.server.error")
    return JSONResponse(status_code=500, content=body.model_dump())


# -------------------------------
# Health Check
# -------------------------------
@app.get("/health", tags=["Health"])
async def health(request: Request):
    return make_success_response(request, data={"status": "ok"}, message="health.ok")
