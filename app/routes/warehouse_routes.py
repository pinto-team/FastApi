from fastapi import APIRouter, HTTPException, Query, Request
from uuid import UUID
from typing import Optional, List

from app.models.warehouse import Warehouse, WarehouseCreate, WarehouseUpdate
from app.models.response import ApiSuccessResponse, SuccessMeta, PaginationMeta, make_success_response, make_pagination_meta
from app.services.warehouse_service import warehouse_service

router = APIRouter()

@router.get("", response_model=ApiSuccessResponse[List[Warehouse]])
async def list_warehouses(
    request: Request,
    name: Optional[str] = Query(None, description="Filter by warehouse name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    filters = {}
    if name:
        filters["name"] = name
    if location:
        filters["location"] = location

    items, total = await warehouse_service.list(filters, page, limit)

    pagination = make_pagination_meta(page=page, limit=limit, total=total)
    return make_success_response(request, data=items, message="warehouses.list.success", pagination=pagination)

@router.post("", response_model=ApiSuccessResponse[Warehouse], status_code=201)
async def create_warehouse(request: Request, payload: WarehouseCreate):
    created = await warehouse_service.create(payload)
    return make_success_response(request, data=created, message="warehouses.create.success", code="201")

@router.get("/{warehouse_id}", response_model=ApiSuccessResponse[Warehouse])
async def get_warehouse(request: Request, warehouse_id: UUID):
    warehouse = await warehouse_service.get(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return make_success_response(request, data=warehouse, message="warehouses.get.success")

@router.put("/{warehouse_id}", response_model=ApiSuccessResponse[Warehouse])
async def update_warehouse(request: Request, warehouse_id: UUID, payload: WarehouseUpdate):
    updated = await warehouse_service.update(warehouse_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return make_success_response(request, data=updated, message="warehouses.update.success")

@router.delete("/{warehouse_id}", response_model=ApiSuccessResponse[dict])
async def delete_warehouse(request: Request, warehouse_id: UUID):
    ok = await warehouse_service.delete(warehouse_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return make_success_response(request, data={"status": "deleted"}, message="warehouses.delete.success")
