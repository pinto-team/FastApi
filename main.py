from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import get_settings
from app.routes.product_routes import router as products_router
from app.routes.store_routes import router as stores_router
from app.routes.category_routes import router as categories_router
from app.routes.brand_routes import router as brands_router
from app.routes.warehouse_routes import router as warehouses_router
from app.routes.user_routes import router as users_router
from app.routes.upload_routes import router as upload_router
from app.models.response import (
    make_error_response,
    make_success_response,
    ErrorDetail,
)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title=settings.project_name,
    description="🛒 Mock API server for frontend testing until backend is ready",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # Redoc UI
    openapi_url="/openapi.json"
)

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ✅ Routers
app.mount("/static", StaticFiles(directory="uploads"), name="static")
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(upload_router, prefix="/files", tags=["Upload"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(stores_router, prefix="/stores", tags=["Stores"])
app.include_router(categories_router, prefix="/categories", tags=["Categories"])
app.include_router(brands_router, prefix="/brands", tags=["Brands"])
app.include_router(warehouses_router, prefix="/warehouses", tags=["Warehouses"])

# ✅ Lightweight request context middleware (trace/correlation/request IDs)
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    # Accept external correlation ID if provided, otherwise generate
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    request.state.correlation_id = correlation_id
    request.state.trace_id = str(uuid4())
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    # Propagate IDs back in headers for debugging
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Trace-ID"] = request.state.trace_id
    response.headers["X-Request-ID"] = request.state.request_id
    return response


# ✅ Centralized error handlers with unified body
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for err in exc.errors():
        field_path = ".".join([str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")])
        details.append(ErrorDetail(field=field_path or None, message=err.get("msg", "Invalid input")))
    body = make_error_response(request, code=422, message="validation.error", errors=details)
    return JSONResponse(status_code=422, content=body.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Let HTTPException fall through to default unless we wrap all exceptions
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        body = make_error_response(request, code=exc.status_code, message=str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())
    body = make_error_response(request, code=500, message="internal.server.error")
    return JSONResponse(status_code=500, content=body.model_dump())


@app.get("/health", tags=["Health"])
async def health(request: Request):
    return make_success_response(request, data={"status": "ok"}, message="health.ok")
