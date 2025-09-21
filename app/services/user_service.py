from uuid import UUID, uuid4
from datetime import datetime
from fastapi import HTTPException
from typing import List, Tuple

from app.db.mongo import db
from app.models.user import User, UserRegister, UserUpdate


class UserService:
    def __init__(self):
        self.collection = db["users"]

    # -------- Create --------
    async def create(self, data: UserRegister) -> User:
        now = datetime.utcnow()
        data_dict = data.dict(exclude_unset=True)

        # الزامی‌ها
        if not data_dict.get("first_name") or not data_dict.get("last_name") or not data_dict.get("phone"):
            raise HTTPException(status_code=400, detail="first_name, last_name and phone are required")

        new_id = uuid4()
        user_doc = {
            "_id": str(new_id),   # Mongo _id
            "id": new_id,         # اپلیکیشن UUID
            "first_name": data_dict["first_name"],
            "last_name": data_dict["last_name"],
            "phone": data_dict["phone"],
            "email": data_dict.get("email"),
            "region": data_dict.get("region"),

            # مقادیر پیش‌فرض سمت سرور
            "email_verified": False,
            "phone_verified": False,
            "referral_code": None,
            "inviter_user_id": None,
            "status": "ACTIVE",

            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
            "last_login_at": None,
        }

        await self.collection.insert_one(user_doc)
        return User(**user_doc)

    # -------- Get --------
    async def get(self, id_: UUID) -> User | None:
        doc = await self.collection.find_one({"id": id_})
        return User(**doc) if doc else None

    # -------- Update --------
    async def update(self, id_: UUID, data: UserUpdate) -> User | None:
        patch = data.dict(exclude_unset=True)
        if patch:
            patch["updated_at"] = datetime.utcnow()
            await self.collection.update_one({"id": id_}, {"$set": patch})
        doc = await self.collection.find_one({"id": id_})
        return User(**doc) if doc else None

    # -------- Delete --------
    async def delete(self, id_: UUID) -> bool:
        res = await self.collection.delete_one({"id": id_})
        return res.deleted_count > 0

    # -------- List with pagination --------
    async def list(self, filters: dict | None, page: int, limit: int) -> Tuple[List[User], int]:
        q = {k: v for k, v in (filters or {}).items() if v is not None}
        cursor = (
            self.collection
            .find(q)
            .skip((page - 1) * limit)
            .limit(limit)
            .sort("created_at", -1)
        )
        items = [User(**doc) async for doc in cursor]
        total = await self.collection.count_documents(q)
        return items, total


user_service = UserService()
