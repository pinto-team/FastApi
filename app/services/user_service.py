from app.models.user import User, UserCreate, UserUpdate
from .base import MongoCRUD


class UserService(MongoCRUD):
    def __init__(self):
        super().__init__(
            collection="users",
            model_cls=User,
            create_cls=UserCreate,
            update_cls=UserUpdate
        )

    # می‌تونی متدهای خاص مثل get_by_email یا get_by_username هم اضافه کنی
    async def get_by_email(self, email: str) -> User | None:
        doc = await self.collection.find_one({"email": email})
        if not doc:
            return None
        return User(**doc)


user_service = UserService()
