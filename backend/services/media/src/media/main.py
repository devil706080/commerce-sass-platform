from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from media.auth import require_tenant_admin
from media.config import load_settings
from media.service import MediaService

app = FastAPI(title="Media Service", version="0.1.0")
app.state.settings = load_settings()

def service(request: Request, _identity=Depends(require_tenant_admin)) -> MediaService:
    return MediaService(request.state.tenant_settings)

@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/api/v1/media", status_code=201)
async def upload_media(file: UploadFile, _identity=Depends(require_tenant_admin), media: MediaService = Depends(service)):
    return await media.upload(file)

@app.delete("/api/v1/media/{asset_id}", status_code=204)
def delete_media(asset_id: UUID, _identity=Depends(require_tenant_admin), media: MediaService = Depends(service)):
    try: media.delete(asset_id)
    except LookupError as exc: raise HTTPException(404, "Media asset not found") from exc

@app.get("/api/v1/media/{asset_id}/content")
def media_content(asset_id: UUID, _identity=Depends(require_tenant_admin), media: MediaService = Depends(service)):
    try: path, content_type = media.content(asset_id)
    except LookupError as exc: raise HTTPException(404, "Media asset not found") from exc
    return FileResponse(path, media_type=content_type, headers={"Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff"})
