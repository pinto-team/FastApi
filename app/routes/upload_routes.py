import uuid
from pathlib import Path
import shutil
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.services.file_service import file_service
from app.models.file import File as FileModel, FileCreate
from app.models.response import make_success_response

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}

class UploadResponse(BaseModel):
    files: List[FileModel]

@router.post("/upload", response_model=UploadResponse)
async def upload(files: List[UploadFile] = File(...)):
    results = []
    for upload in files:
        filename = Path(upload.filename).name
        ext = filename.split(".")[-1].lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(status_code=400, detail=f"فرمت فایل پشتیبانی نمی‌شود: {filename}")

        unique_filename = f"{uuid.uuid4()}.{ext}"
        dest = UPLOAD_DIR / unique_filename
        try:
            with dest.open("wb") as buffer:
                shutil.copyfileobj(upload.file, buffer)
            file_data = FileCreate(
                url=f"/static/{unique_filename}",
                filename=filename,
                content_type=upload.content_type,
                size=upload.size
            )
            created = await file_service.create(file_data)
            results.append(created)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"خطا در ذخیره فایل: {str(e)}")

    # Upload API keeps its own shape as discussed, but we can still wrap if needed later.
    return {"files": results}