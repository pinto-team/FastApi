from uuid import UUID
from typing import List, Optional
import logging

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

from app.models.category import Category, CategoryCreate, CategoryUpdate, ReorderCategory
from app.services.category_service import category_service
from app.models.response import ApiSuccessResponse, make_success_response, make_pagination_meta

logger = logging.getLogger("app.routes.category_routes")
router = APIRouter()


# -------------------------------
# Schemas specific to routes
# -------------------------------
class ReorderSinglePayload(BaseModel):
    order: int = Field(..., ge=0, description="New order index for the category")


# -------------------------------
# Fixed routes FIRST (no conflict)
# -------------------------------
@router.put("/reorder", response_model=ApiSuccessResponse[dict])
async def reorder_categories(request: Request, payload: List[ReorderCategory]):
    """
    Bulk reorder for categories that share the same parent.
    Body: [{ "id": "<uuid>", "order": <int> }, ...]
    """
    logger.debug(f"PUT /categories/reorder with payload: {payload}")
    try:
        await category_service.reorder(payload)
        return make_success_response(
            request, data={"status": "reordered"}, message="Categories reordered successfully"
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{category_id}/reorder", response_model=ApiSuccessResponse[dict])
async def reorder_single_category(request: Request, category_id: UUID, payload: ReorderSinglePayload):
    """
    Reorder a single category.
    Path: /categories/{category_id}/reorder
    Body: { "order": <int> }
    """
    logger.debug(f"PUT /categories/{category_id}/reorder with payload: {payload}")
    try:
        await category_service.reorder_single(str(category_id), payload.order)
        return make_success_response(
            request, data={"status": "reordered"}, message="Category reordered successfully"
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


# -------------------------------
# List (no conflict)
# -------------------------------
@router.get("/", response_model=ApiSuccessResponse[List[Category]])
async def list_categories(
    request: Request,
    name: Optional[str] = Query(None, description="Filter by category name"),
    parent_id: Optional[str] = Query(None, description="Filter by parent category"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    logger.debug(f"GET /categories with filters name={name}, parent_id={parent_id}")
    filters = {}
    if name:
        filters["name"] = name
    if parent_id:
        filters["parent_id"] = parent_id

    items, total = await category_service.list(filters, page, limit)
    pagination = make_pagination_meta(page=page, limit=limit, total=total)
    return make_success_response(
        request,
        data=items,
        message="Categories retrieved successfully",
        pagination=pagination,
    )


# -------------------------------
# Parametric routes (UUID only)
# -------------------------------
@router.get("/{category_id}", response_model=ApiSuccessResponse[Category])
async def get_category(request: Request, category_id: UUID):
    logger.debug(f"GET /categories/{category_id}")
    category = await category_service.get(str(category_id))
    if not category:
        raise HTTPException(404, "Category not found")
    return make_success_response(request, data=category, message="Category retrieved successfully")


@router.post("/", response_model=ApiSuccessResponse[Category], status_code=201)
async def create_category(request: Request, payload: CategoryCreate):
    logger.info(f"POST /categories with payload: {payload}")
    logger.info(f"Payload dump: {payload.model_dump()}")

    try:
        created = await category_service.create(payload)
        return make_success_response(
            request, data=created, message="Category created successfully", code="201"
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{category_id}", response_model=ApiSuccessResponse[Category])
async def update_category(request: Request, category_id: UUID, payload: CategoryUpdate):
    logger.debug(f"PUT /categories/{category_id} with payload: {payload}")
    try:
        updated = await category_service.update(str(category_id), payload)
        if not updated:
            raise HTTPException(404, "Category not found")
        return make_success_response(
            request, data=updated, message="Category updated successfully"
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.patch("/{category_id}/order", response_model=ApiSuccessResponse[Category])
async def patch_category_order(request: Request, category_id: UUID, payload: ReorderSinglePayload):
    logger.debug(f"PATCH /categories/{category_id}/order with payload: {payload}")
    try:
        updated = await category_service.update(str(category_id), CategoryUpdate(order=payload.order))
        if not updated:
            raise HTTPException(404, "Category not found")
        return make_success_response(
            request, data=updated, message="Category order updated successfully"
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{category_id}", response_model=ApiSuccessResponse[dict])
async def delete_category(request: Request, category_id: UUID):
    logger.debug(f"DELETE /categories/{category_id}")
    try:
        success = await category_service.delete(str(category_id))
        if not success:
            raise HTTPException(404, "Category not found")
        return make_success_response(
            request, data={"status": "deleted"}, message="Category deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
