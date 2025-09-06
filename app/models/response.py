from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar
from fastapi import Request

T = TypeVar("T")


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str


class ApiErrorResponse(BaseModel):
    code: int
    message: str
    errors: List[ErrorDetail]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: Optional[int] = None
    has_next: Optional[bool] = None
    has_previous: Optional[bool] = None


class SuccessMeta(BaseModel):
    message: str
    status: Optional[str] = "success"
    code: Optional[str] = "200"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    query: Optional[str] = None
    host: Optional[str] = None
    additional: Dict[str, Any] = {}
    pagination: Optional[PaginationMeta] = None


class ApiSuccessResponse(BaseModel, Generic[T]):
    data: Optional[T]
    meta: SuccessMeta


# ---------- Helper builders for consistent responses ----------

def make_pagination_meta(page: int, limit: int, total: int) -> PaginationMeta:
    total_pages: Optional[int] = None
    has_next: Optional[bool] = None
    has_previous: Optional[bool] = None

    if limit > 0:
        total_pages = (total + limit - 1) // limit
        has_next = (page * limit) < total
        has_previous = page > 1

    return PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )


def make_success_response(
    request: Request,
    *,
    data: T | None,
    message: str,
    code: str = "200",
    status: str = "success",
    pagination: Optional[PaginationMeta] = None,
    additional: Optional[Dict[str, Any]] = None,
) -> ApiSuccessResponse[T]:
    meta = SuccessMeta(
        message=message,
        status=status,
        code=code,
        timestamp=datetime.utcnow().isoformat(),
        trace_id=getattr(request.state, "trace_id", None),
        correlation_id=getattr(request.state, "correlation_id", None),
        request_id=getattr(request.state, "request_id", None),
        method=request.method,
        path=request.url.path,
        query=str(request.url.query) if request.url.query else None,
        host=request.client.host if request.client else None,
        additional=additional or {},
        pagination=pagination,
    )
    return ApiSuccessResponse(data=data, meta=meta)


def make_error_response(
    request: Optional[Request],
    *,
    code: int,
    message: str,
    errors: Optional[List[ErrorDetail]] = None,
) -> ApiErrorResponse:
    return ApiErrorResponse(
        code=code,
        message=message,
        errors=errors or [],
        timestamp=datetime.utcnow().isoformat(),
    )
