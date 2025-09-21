from fastapi import APIRouter, Request, HTTPException, Query
from uuid import UUID
from typing import List, Optional

from app.models.user import User, UserRegister, UserUpdate
from app.models.response import ApiSuccessResponse, make_success_response, make_pagination_meta
from app.services.user_service import user_service

router = APIRouter()

# ---------- Create ----------
@router.post("", response_model=ApiSuccessResponse[User], status_code=201)
async def register_user(request: Request, payload: UserRegister):
    user = await user_service.create(payload)
    return make_success_response(request, data=user, message="users.register.success", code="201")

# ---------- List ----------
@router.get("", response_model=ApiSuccessResponse[List[User]])
async def list_users(
    request: Request,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    filters = {"first_name": first_name, "last_name": last_name, "phone": phone}
    items, total = await user_service.list(filters, page, limit)
    pagination = make_pagination_meta(page, limit, total)
    return make_success_response(request, data=items, message="users.list.success", pagination=pagination)

# ---------- Get by ID ----------
@router.get("/{user_id}", response_model=ApiSuccessResponse[User])
async def get_user(request: Request, user_id: UUID):
    user = await user_service.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return make_success_response(request, data=user, message="users.get.success")

# ---------- Update ----------
@router.put("/{user_id}", response_model=ApiSuccessResponse[User])
async def update_user(request: Request, user_id: UUID, payload: UserUpdate):
    updated = await user_service.update(user_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return make_success_response(request, data=updated, message="users.update.success")

# ---------- Delete ----------
@router.delete("/{user_id}", response_model=ApiSuccessResponse[dict])
async def delete_user(request: Request, user_id: UUID):
    ok = await user_service.delete(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return make_success_response(request, data={"status": "deleted"}, message="users.delete.success")
