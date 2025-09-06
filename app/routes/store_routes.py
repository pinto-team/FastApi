from fastapi import APIRouter, HTTPException, Query, Request
from uuid import UUID
from typing import List, Optional

from app.models.store import Store, StoreCreate, StoreUpdate
from app.services.store_service import store_service
from app.models.response import ApiSuccessResponse, SuccessMeta, PaginationMeta, make_success_response, make_pagination_meta

router = APIRouter()

@router.get('', response_model=ApiSuccessResponse[List[Store]])
async def list_stores(
    request: Request,
    search: Optional[str] = Query(None, description="Search stores by name, address or phone"),
    sort_by: Optional[str] = Query(None, description="Sort by 'name' or 'created_at' (asc/desc)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    stores = await store_service.list()

    # فیلتر با search
    if search:
        stores = [
            s for s in stores
            if search.lower() in s.name.lower()
            or (s.address and search.lower() in s.address.lower())
            or (s.phone and search.lower() in s.phone.lower())
        ]

    # مرتب‌سازی
    if sort_by:
        if sort_by == "name":
            stores = sorted(stores, key=lambda s: s.name)
        elif sort_by == "name_desc":
            stores = sorted(stores, key=lambda s: s.name, reverse=True)
        elif sort_by == "created_at":
            stores = sorted(stores, key=lambda s: s.created_at)
        elif sort_by == "created_at_desc":
            stores = sorted(stores, key=lambda s: s.created_at, reverse=True)

    total = len(stores)
    start = (page - 1) * limit
    end = start + limit
    paged = stores[start:end]

    pagination = make_pagination_meta(page=page, limit=limit, total=total)
    return make_success_response(request, data=paged, message="stores.list.success", pagination=pagination)

@router.get('/{store_id}', response_model=ApiSuccessResponse[Store])
async def get_store(request: Request, store_id: UUID):
    store = await store_service.get(store_id)
    if not store:
        raise HTTPException(404, 'Store not found')
    return make_success_response(request, data=store, message="stores.get.success")

@router.post('', response_model=ApiSuccessResponse[Store], status_code=201)
async def create_store(request: Request, payload: StoreCreate):
    created = await store_service.create(payload)
    return make_success_response(request, data=created, message="stores.create.success", code="201")

@router.put('/{store_id}', response_model=ApiSuccessResponse[Store])
async def update_store(request: Request, store_id: UUID, payload: StoreUpdate):
    store = await store_service.update(store_id, payload)
    if not store:
        raise HTTPException(404, 'Store not found')
    return make_success_response(request, data=store, message="stores.update.success")

@router.delete('/{store_id}', response_model=ApiSuccessResponse[dict])
async def delete_store(request: Request, store_id: UUID):
    success = await store_service.delete(store_id)
    if not success:
        raise HTTPException(404, 'Store not found')
    return make_success_response(request, data={'status': 'deleted'}, message="stores.delete.success")
