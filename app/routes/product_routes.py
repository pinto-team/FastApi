from fastapi import APIRouter, HTTPException, Query, Request
from uuid import UUID
from typing import List, Optional

from app.models.product import ProductResponse, ProductCreate, ProductUpdate
from app.models.response import (
    ApiSuccessResponse,
    make_success_response,
    make_pagination_meta,
)
from app.services.product_service import product_service

router = APIRouter()


@router.get("", response_model=ApiSuccessResponse[List[ProductResponse]])
async def list_products(
    request: Request,
    search: Optional[str] = Query(None, description="Search in name, description, tags"),
    brand_id: Optional[UUID] = Query(None),
    category_id: Optional[UUID] = Query(None),
    tags: Optional[List[str]] = Query(None, description="Filter by any of these tags"),
    is_active: Optional[bool] = Query(None),
    include_deleted: bool = Query(False),
    sort: Optional[str] = Query(
        None,
        description="Sort key, one of: name_asc, name_desc, created_asc, created_desc (default: created_desc)",
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    items, total = await product_service.list(
        search=search,
        brand_id=brand_id,
        category_id=category_id,
        tags=tags,
        is_active=is_active,
        include_deleted=include_deleted,
        sort=sort,
        page=page,
        limit=limit,
    )
    pagination = make_pagination_meta(page=page, limit=limit, total=total)
    return make_success_response(request, data=items, message="products.list.success", pagination=pagination)


@router.get("/{product_id}", response_model=ApiSuccessResponse[ProductResponse])
async def get_product(request: Request, product_id: UUID, include_deleted: bool = Query(False)):
    product = await product_service.get(product_id, include_deleted=include_deleted)
    if not product:
        raise HTTPException(404, "Product not found")
    return make_success_response(request, data=product, message="products.get.success")


@router.post("", response_model=ApiSuccessResponse[ProductResponse], status_code=201)
async def create_product(request: Request, payload: ProductCreate):
    created = await product_service.create(payload)
    product = await product_service.get(created.id)
    return make_success_response(request, data=product, message="products.create.success", code="201")


@router.put("/{product_id}", response_model=ApiSuccessResponse[ProductResponse])
async def update_product(request: Request, product_id: UUID, payload: ProductUpdate):
    updated = await product_service.update(product_id, payload)
    if not updated:
        raise HTTPException(404, "Product not found")
    product = await product_service.get(product_id)
    return make_success_response(request, data=product, message="products.update.success")


@router.delete("/{product_id}", response_model=ApiSuccessResponse[dict])
async def delete_product(request: Request, product_id: UUID):
    success = await product_service.delete(product_id)
    if not success:
        raise HTTPException(404, "Product not found")
    return make_success_response(request, data={"status": "deleted"}, message="products.delete.success")
