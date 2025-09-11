from uuid import UUID, uuid4
from datetime import datetime

from fastapi import HTTPException

from app.db.mongo import db
from app.models.file import File, FileCreate, FileUpdate
from app.services.base import MongoCRUD, _serialize


class FileService(MongoCRUD):
    def __init__(self):
        super().__init__(
            collection="files",
            model_cls=File,
            create_cls=FileCreate,
            update_cls=FileUpdate,
        )

    async def create(self, data: FileCreate) -> File:
        """
        ایجاد فایل جدید
        """
        now = datetime.utcnow()
        data_dict = data.model_dump(exclude_unset=True)

        # نگه‌داری UUID در id و ذخیره به عنوان _id در Mongo
        new_id = uuid4()
        data_dict["_id"] = str(new_id)
        data_dict["id"] = new_id
        data_dict.setdefault("created_at", now)
        data_dict.setdefault("updated_at", now)

        await self.collection.insert_one(data_dict)
        return File(**data_dict)

    async def get(self, id_: UUID) -> File | None:
        """
        بر اساس شناسه فایل را برمی‌گرداند یا None اگر وجود نداشت.
        """
        doc = await self.collection.find_one({"_id": str(id_)})
        return File(**_serialize(doc)) if doc else None

    async def ensure_exists(self, id_: UUID) -> File:
        """
        اگر فایل با شناسه داده‌شده وجود نداشته باشد، خطای 400 برمی‌گرداند.
        """
        f = await self.get(id_)
        if not f:
            raise HTTPException(status_code=400, detail=f"فایل با شناسه {id_} پیدا نشد.")
        return f

    async def update(self, id_: UUID, data: FileUpdate) -> File | None:
        """
        بروزرسانی فایل
        """
        patch = data.model_dump(exclude_unset=True)
        patch["updated_at"] = datetime.utcnow()

        await self.collection.update_one({"_id": str(id_)}, {"$set": patch})
        doc = await self.collection.find_one({"_id": str(id_)})
        return File(**_serialize(doc)) if doc else None

    async def delete(self, id_: UUID) -> bool:
        """
        حذف فایل
        """
        res = await self.collection.delete_one({"_id": str(id_)})
        return res.deleted_count > 0


file_service = FileService()
__all__ = ["file_service", "FileService"]
