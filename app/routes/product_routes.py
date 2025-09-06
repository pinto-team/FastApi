from fastapi import APIRouter, HTTPException, Query, Request
from uuid import UUID
from typing import List, Optional

from app.models.product import ProductResponse, ProductCreate, ProductUpdate
from app.models.response import ApiSuccessResponse, SuccessMeta, PaginationMeta, make_success_response, make_pagination_meta
from app.services.product_service import product_service   # ✅ فقط این

router = APIRouter()

@router.get("", response_model=ApiSuccessResponse[List[ProductResponse]])
async def list_products(
    request: Request,
    search: Optional[str] = Query(None, description="Search in name, description, tags"),
    sort_by_price: Optional[str] = Query(None, description="Sort by price: 'asc' or 'desc'"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    items, total = await product_service.list(search=search, sort_by_price=sort_by_price, page=page, limit=limit)
    pagination = make_pagination_meta(page=page, limit=limit, total=total)
    return make_success_response(request, data=items, message="products.list.success", pagination=pagination)

@router.get("/{product_id}", response_model=ApiSuccessResponse[ProductResponse])
async def get_product(request: Request, product_id: UUID):
    product = await product_service.get(product_id)
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
