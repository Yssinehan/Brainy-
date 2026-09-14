"""Validation securisee des fichiers uploades (audio/image) avant traitement."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_MIMETYPES = {
    "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp4", "audio/ogg",
    "image/png", "image/jpeg", "image/webp",
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


async def validate_and_save(upload: UploadFile, max_size: int = MAX_FILE_SIZE) -> str:
    filename = upload.filename or "upload"
    file_ext = Path(filename).suffix.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extension non autorisee: {file_ext or '(aucune)'}")

    if upload.content_type and upload.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(status_code=400, detail=f"Type MIME non autorise: {upload.content_type}")

    content = await upload.read(max_size + 1)

    if not content:
        raise HTTPException(status_code=400, detail="Fichier vide")

    if len(content) > max_size:
        raise HTTPException(status_code=413, detail=f"Fichier trop volumineux. Max: {max_size / 1024 / 1024:.1f} MB")

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(content)
        return tmp.name