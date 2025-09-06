from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime


class FileBase(BaseModel):
    url: str
    filename: str
    content_type: str | None = None
    size: int | None = None


class FileCreate(FileBase):
    pass


class FileUpdate(BaseModel):
    url: str | None = None
    filename: str | None = None
    content_type: str | None = None
    size: int | None = None


class File(FileBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
