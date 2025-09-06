from uuid import UUID
from typing import List, Optional
from pymongo import ASCENDING, DESCENDING
from datetime import datetime

from . import file_service
from .base import MongoCRUD, _serialize
from app.models.product import (
    Product, ProductCreate, ProductUpdate, ProductResponse, WarehouseAvailabilityResponse
)
from app.models.store import Store
from app.models.category import Category
from app.models.brand import Brand
from app.models.warehouse import Warehouse
from app.db.mongo import db
from app.services.category_service import category_service
from app.services.brand_service import brand_service


class ProductService(MongoCRUD):
    def __init__(self):
        super().__init__(
            collection="products",
            model_cls=Product,
            create_cls=ProductCreate,
            update_cls=ProductUpdate
        )

    async def create(self, payload: ProductCreate) -> Product:
        # Validate foreign keys
        if payload.brand_id:
            brand = await brand_service.get(payload.brand_id)
            if not brand:
                raise ValueError(f"Brand with id {payload.brand_id} does not exist")
        if payload.category_id:
            category = await category_service.get(payload.category_id)
            if not category:
                raise ValueError(f"Category with id {payload.category_id} does not exist")
        return await super().create(payload)

    async def update(self, id_: UUID, patch: ProductUpdate) -> Product | None:
        # FK checks on update
        if patch.brand_id:
            brand = await brand_service.get(patch.brand_id)
            if not brand:
                raise ValueError(f"Brand with id {patch.brand_id} does not exist")
        if patch.category_id:
            category = await category_service.get(patch.category_id)
            if not category:
                raise ValueError(f"Category with id {patch.category_id} does not exist")

        # ensure updated_at
        patch_dict = patch.dict(exclude_unset=True)
        patch_dict["updated_at"] = datetime.utcnow()
        return await super().update(id_, ProductUpdate(**patch_dict))

    async def list(
        self,
        search: Optional[str] = None,
        sort_by_price: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[ProductResponse], int]:
        query = {}
        if search:
            query = {
                "$or": [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"full_name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}},
                    {"tags": {"$regex": search, "$options": "i"}},
                ]
            }

        cursor = self.collection.find(query)
        if sort_by_price:
            order = ASCENDING if sort_by_price == "asc" else DESCENDING
            cursor = cursor.sort("price", order)

        cursor = cursor.skip((page - 1) * limit).limit(limit)
        products = [self.model_cls(**_serialize(doc)) async for doc in cursor]
        total = await self.collection.count_documents(query)
        return await self._populate(products), total

    async def get(self, id_: UUID) -> ProductResponse | None:
        product = await super().get(id_)
        if not product:
            return None
        populated = await self._populate([product])
        return populated[0]

    async def _populate(self, products: List[Product]) -> List[ProductResponse]:
        responses: List[ProductResponse] = []
        for p in products:
            data = p.model_dump()

            # Store
            if getattr(p, "store_id", None):
                store_doc = await db["stores"].find_one({"id": p.store_id})
                if store_doc:
                    data["store"] = Store(**_serialize(store_doc))

            # Category
            if p.category_id:
                cat_doc = await db["categories"].find_one({"id": p.category_id})
                if cat_doc:
                    data["category"] = Category(**_serialize(cat_doc))

            # Brand
            if p.brand_id:
                brand_doc = await db["brands"].find_one({"id": p.brand_id})
                if brand_doc:
                    bd = _serialize(brand_doc)
                    bd.pop("_id", None)  # _id لازم نیست
                    bd["id"] = str(p.brand_id)  # 👈 اطمینان: id = UUID محصول
                    data["brand"] = Brand(**bd)

            # Warehouses availability
            wa_list = []
            for wa in (getattr(p, "warehouse_availability", []) or []):
                wa_dict = wa.model_dump() if hasattr(wa, "model_dump") else dict(wa)
                w_doc = await db["warehouses"].find_one({"id": wa_dict.get("warehouse_id")})
                if w_doc:
                    wa_dict["warehouse"] = Warehouse(**_serialize(w_doc))
                wa_list.append(WarehouseAvailabilityResponse(**wa_dict))
            data["warehouse_availability"] = wa_list

            # Images
            imgs = []
            for fid in (getattr(p, "images", []) or []):
                try:
                    f_doc = await file_service.get(fid)
                    if f_doc:
                        imgs.append(f_doc)
                except Exception:
                    # در صورت نبود سرویس فایل یا خطا، فقط رد می‌شویم
                    pass
            data["images"] = imgs

            responses.append(ProductResponse(**data))
        return responses


# Instance for import in routes
product_service = ProductService()
__all__ = ["ProductService", "product_service"]
