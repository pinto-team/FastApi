from pydantic import BaseModel
from uuid import UUID, uuid4
from datetime import datetime

from app.db.mongo import db
from app.models.file import File, FileCreate, FileUpdate

class MongoCRUD:
    def __init__(self, collection: str, model_cls: type[BaseModel], create_cls: type[BaseModel], update_cls: type[BaseModel]):
        self.collection = db[collection]
        self.model_cls = model_cls
        self.create_cls = create_cls
        self.update_cls = update_cls

    async def create(self, data: BaseModel):
        data_dict = data.dict(exclude_unset=True)
        data_dict["id"] = data_dict.get("id") or uuid4()
        data_dict["created_at"] = data_dict.get("created_at") or datetime.utcnow()
        await self.collection.insert_one(data_dict)
        return self.model_cls(**data_dict)

    async def get(self, id_: UUID):
        doc = await self.collection.find_one({"id": id_})
        return self.model_cls(**doc) if doc else None

    async def update(self, id_: UUID, data: BaseModel):
        patch = data.dict(exclude_unset=True)
        await self.collection.update_one({"id": id_}, {"$set": patch})
        doc = await self.collection.find_one({"id": id_})
        return self.model_cls(**doc) if doc else None

    async def delete(self, id_: UUID):
        res = await self.collection.delete_one({"id": id_})
        return res.deleted_count > 0

class FileService(MongoCRUD):
    def __init__(self):
        super().__init__("files", File, FileCreate, FileUpdate)

file_service = FileService()
