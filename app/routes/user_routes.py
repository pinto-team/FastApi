from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional
from uuid import UUID

from app.models.user import User, UserCreate, UserUpdate
from app.services.user_service import user_service
from app.models.response import ApiSuccessResponse, SuccessMeta, PaginationMeta, make_success_response

router = APIRouter()


@router.get("", response_model=ApiSuccessResponse[List[User]])
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    # Base service currently returns all; emulate pagination in route for consistency
    items = await user_service.list()
    total = len(items)
    start = (page - 1) * limit
    end = start + limit
    paged = items[start:end]
    meta = SuccessMeta(
        message="users.list.success",
        method=request.method,
        path=request.url.path,
        host=request.client.host if request.client else None,
        pagination=PaginationMeta(page=page, limit=limit, total=total,
                                   total_pages=(total + limit - 1) // limit if limit else None,
                                   has_next=end < total,
                                   has_previous=page > 1),
    )
    return ApiSuccessResponse(data=paged, meta=meta)


@router.get("/{user_id}", response_model=ApiSuccessResponse[User])
async def get_user(request: Request, user_id: UUID):
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return make_success_response(request, data=user, message="users.get.success")


@router.post("", response_model=ApiSuccessResponse[User], status_code=201)
async def create_user(request: Request, payload: UserCreate):
    created = await user_service.create(payload)
    return make_success_response(request, data=created, message="users.create.success", code="201")


@router.put("/{user_id}", response_model=ApiSuccessResponse[User])
async def update_user(request: Request, user_id: UUID, payload: UserUpdate):
    user = await user_service.update(user_id, payload)
    if not user:
        raise HTTPException(404, "User not found")
    return make_success_response(request, data=user, message="users.update.success")


@router.delete("/{user_id}", response_model=ApiSuccessResponse[dict])
async def delete_user(request: Request, user_id: UUID):
    success = await user_service.delete(user_id)
    if not success:
        raise HTTPException(404, "User not found")
    return make_success_response(request, data={"status": "deleted"}, message="users.delete.success")
