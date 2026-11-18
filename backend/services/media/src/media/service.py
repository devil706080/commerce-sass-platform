from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from media.config import Settings
from media.repository import MediaRepository


class MediaService:
    def __init__(self, settings: Settings): self.settings, self.repository = settings, MediaRepository(settings)

    async def upload(self, upload: UploadFile):
        if upload.content_type not in {"image/jpeg", "image/png", "image/webp"}: raise HTTPException(415, "Only JPEG, PNG, and WebP images are accepted")
        raw = await upload.read(self.settings.max_upload_bytes + 1)
        if not raw or len(raw) > self.settings.max_upload_bytes: raise HTTPException(413, "Image must be no larger than 5 MB")
        try:
            with Image.open(BytesIO(raw)) as source:
                source.verify()
            with Image.open(BytesIO(raw)) as source:
                if source.width * source.height > self.settings.max_pixels: raise HTTPException(413, "Image dimensions are too large")
                image = source.convert("RGB"); output = BytesIO(); image.save(output, format="WEBP", quality=88, method=6)
                width, height, encoded = image.width, image.height, output.getvalue()
        except (UnidentifiedImageError, OSError, ValueError):
            raise HTTPException(422, "Invalid image content") from None
        asset_id = uuid4(); key = f"{asset_id}.webp"; target = self.settings.storage_root / key
        self.settings.storage_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(encoded)
        try: self.repository.create(asset_id, upload.filename or "image", len(encoded), width, height, key)
        except Exception:
            target.unlink(missing_ok=True); raise
        return {"id": asset_id, "content_type": "image/webp", "byte_size": len(encoded), "width": width, "height": height, "url": f"/api/v1/media/{asset_id}/content"}

    def content(self, asset_id: UUID):
        key, content_type, *_ = self.repository.get(asset_id); path = self.settings.storage_root / key
        if not path.is_file(): raise LookupError("Media asset not found")
        return path, content_type

    def delete(self, asset_id: UUID):
        key = self.repository.delete(asset_id); (self.settings.storage_root / key).unlink(missing_ok=True)
