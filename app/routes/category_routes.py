from fastapi import APIRouter, HTTPException, Query, Request
from uuid import UUID
from typing import List, Optional

from app.models.category import Category, CategoryCreate, CategoryUpdate
from app.services.category_service import category_service
from app.models.response import ApiSuccessResponse, SuccessMeta, PaginationMeta, make_success_response, make_pagination_meta

router = APIRouter()

@router.get("/", response_model=ApiSuccessResponse[List[Category]])
async def list_categories(
    request: Request,
    name: Optional[str] = Query(None, description="Filter by category name"),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent category"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    filters = {}
    if name:
        filters["name"] = name
    if parent_id:
        filters["parent_id"] = parent_id

    items, total = await category_service.list(filters, page, limit)

    pagination = make_pagination_meta(page=page, limit=limit, total=total)
    return make_success_response(request, data=items, message="categories.list.success", pagination=pagination)

@router.get("/{category_id}", response_model=ApiSuccessResponse[Category])
async def get_category(request: Request, category_id: UUID):
    category = await category_service.get(category_id)
    if not category:
        raise HTTPException(404, "Category not found")

    return make_success_response(request, data=category, message="categories.get.success")

@router.post("/", response_model=ApiSuccessResponse[Category], status_code=201)
async def create_category(request: Request, payload: CategoryCreate):
    created = await category_service.create(payload)
    return make_success_response(request, data=created, message="categories.create.success", code="201")


@router.put("/{category_id}", response_model=ApiSuccessResponse[Category])
async def update_category(request: Request, category_id: UUID, payload: CategoryUpdate):
    category = await category_service.update(category_id, payload)
    if not category:
        raise HTTPException(404, "Category not found")

    return make_success_response(request, data=category, message="categories.update.success")


@router.delete("/{category_id}", response_model=ApiSuccessResponse[dict])
async def delete_category(request: Request, category_id: UUID):
    success = await category_service.delete(category_id)
    if not success:
        raise HTTPException(404, "Category not found")

    return make_success_response(request, data={"status": "deleted"}, message="categories.delete.success")
