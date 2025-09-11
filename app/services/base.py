from typing import Type, TypeVar, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel

from app.db.mongo import db

ModelT = TypeVar("ModelT", bound=BaseModel)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


from bson import ObjectId

def _serialize(doc: dict | None):
    """
    تبدیل داکیومنت Mongo به dict سازگار با مدل Pydantic
    - اگر _id رشته UUID باشد → تبدیل به UUID
    - اگر _id از نوع UUID باشد → همان مقدار
    - اگر _id از نوع ObjectId باشد → تبدیل به str
    """
    if not doc:
        return None
    doc = dict(doc)
    if "_id" in doc:
        _id_val = doc.pop("_id")
        if isinstance(_id_val, UUID):
            doc["id"] = _id_val
        elif isinstance(_id_val, str):
            try:
                doc["id"] = UUID(_id_val)
            except Exception:
                doc["id"] = _id_val  # رشته معمولی (نه UUID معتبر)
        elif isinstance(_id_val, ObjectId):
            doc["id"] = str(_id_val)
        else:
            doc["id"] = str(_id_val)
    return doc


class MongoCRUD:
    def __init__(
        self,
        *,
        collection: str,
        model_cls: Type[ModelT],
        create_cls: Type[CreateT],
        update_cls: Type[UpdateT],
    ):
        self.collection = db[collection]
        self.model_cls = model_cls
        self.create_cls = create_cls
        self.update_cls = update_cls

    async def create(self, payload: CreateT) -> ModelT:
        """
        ایجاد رکورد جدید با id یکتا
        """
        data = payload.model_dump()
        _id = uuid4()
        data["_id"] = str(_id)
        await self.collection.insert_one(data)
        data["id"] = _id
        return self.model_cls(**data)

    async def list(self) -> List[ModelT]:
        """
        لیست تمام رکوردها
        """
        items: List[ModelT] = []
        async for doc in self.collection.find({}):
            data = _serialize(doc)
            if data:
                items.append(self.model_cls(**data))
        return items

    async def get(self, id_: UUID) -> Optional[ModelT]:
        """
        دریافت رکورد بر اساس UUID
        """
        doc = await self.collection.find_one({"_id": str(id_)})
        if not doc:
            return None
        data = _serialize(doc)
        return self.model_cls(**data)

    async def update(self, id_: UUID, patch: UpdateT) -> Optional[ModelT]:
        """
        بروزرسانی رکورد (فقط فیلدهای ارسال‌شده تغییر می‌کنند)
        """
        data = patch.model_dump(exclude_unset=True)
        if data:
            await self.collection.update_one({"_id": str(id_)}, {"$set": data})
        return await self.get(id_)

    async def delete(self, id_: UUID) -> bool:
        """
        حذف رکورد
        """
        res = await self.collection.delete_one({"_id": str(id_)})
        return res.deleted_count == 1
