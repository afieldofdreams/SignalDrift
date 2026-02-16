import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import ALLOWED_EXTENSIONS, settings

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health() -> dict:
    """Health check endpoint for load balancers and Docker health checks."""
    return {"status": "ok"}


@router.get("/hello")
async def hello() -> dict:
    """Hello world endpoint."""
    return {"message": "Mapping Business Resilience."}


@router.post("/documents", status_code=201)
async def upload_document(file: UploadFile) -> dict:
    """Upload a document file. Validates extension against allowlist."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename}"
    dest = settings.upload_path / safe_name

    content = await file.read()
    dest.write_bytes(content)

    return {
        "filename": safe_name,
        "original_name": file.filename,
        "size": len(content),
    }


@router.get("/documents")
async def list_documents() -> dict:
    """List all uploaded documents."""
    files = []
    if settings.upload_path.exists():
        for f in sorted(settings.upload_path.iterdir()):
            if f.is_file():
                stat = f.stat()
                files.append({
                    "filename": f.name,
                    "size": stat.st_size,
                    "uploaded_at": datetime.datetime.fromtimestamp(
                        stat.st_mtime, tz=datetime.UTC
                    ).isoformat(),
                })
    return {"files": files}


@router.delete("/documents/{filename}")
async def delete_document(filename: str) -> dict:
    """Delete an uploaded document by filename."""
    file_path = settings.upload_path / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    # Prevent path traversal
    if file_path.resolve().parent != settings.upload_path.resolve():
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path.unlink()
    return {"deleted": filename}
