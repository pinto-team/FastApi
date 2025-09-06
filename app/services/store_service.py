from app.models.store import Store, StoreCreate, StoreUpdate
from .base import MongoCRUD
from app.services.warehouse_service import warehouse_service


class StoreService(MongoCRUD):
    def __init__(self):
        super().__init__(
            collection="stores",
            model_cls=Store,
            create_cls=StoreCreate,
            update_cls=StoreUpdate
        )

    async def create(self, payload: StoreCreate) -> Store:
        # ✅ بررسی وجود warehouse_ids
        if payload.warehouse_ids:
            for wid in payload.warehouse_ids:
                warehouse = await warehouse_service.get(wid)
                if not warehouse:
                    raise ValueError(f"Warehouse with id {wid} does not exist")

        return await super().create(payload)

    async def update(self, id_, patch: StoreUpdate) -> Store | None:
        # ✅ بررسی warehouse_ids در زمان آپدیت هم
        if patch.warehouse_ids:
            for wid in patch.warehouse_ids:
                warehouse = await warehouse_service.get(wid)
                if not warehouse:
                    raise ValueError(f"Warehouse with id {wid} does not exist")

        return await super().update(id_, patch)


store_service = StoreService()
