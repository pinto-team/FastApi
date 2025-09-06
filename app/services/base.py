from typing import Type, TypeVar, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel

from app.db.mongo import db

ModelT = TypeVar("ModelT", bound=BaseModel)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


def _serialize(doc: dict | None):
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return doc


class MongoCRUD:
    def __init__(self, *, collection: str, model_cls: Type[ModelT], create_cls: Type[CreateT], update_cls: Type[UpdateT]):
        self.collection = db[collection]
        self.model_cls = model_cls
        self.create_cls = create_cls
        self.update_cls = update_cls

    async def create(self, payload: CreateT) -> ModelT:
        data = payload.model_dump()
        _id = str(uuid4())
        data["_id"] = _id
        await self.collection.insert_one(data)
        data["id"] = _id
        return self.model_cls(**data)

    async def list(self) -> List[ModelT]:
        items: List[ModelT] = []
        async for doc in self.collection.find({}):
            data = _serialize(doc)
            items.append(self.model_cls(**data))
        return items

    async def get(self, id_: UUID) -> Optional[ModelT]:
        doc = await self.collection.find_one({"_id": str(id_)})
        if not doc:
            return None
        data = _serialize(doc)
        return self.model_cls(**data)

    async def update(self, id_: UUID, patch: UpdateT) -> Optional[ModelT]:
        data = patch.model_dump(exclude_unset=True)
        if data:
            await self.collection.update_one({"_id": str(id_)}, {"$set": data})
        return await self.get(id_)

    async def delete(self, id_: UUID) -> bool:
        res = await self.collection.delete_one({"_id": str(id_)})
        return res.deleted_count == 1
