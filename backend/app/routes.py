import base64
import datetime
import time
from pathlib import Path

import anthropic
from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import ALLOWED_EXTENSIONS, settings
from app.database import (
    create_prompt,
    create_run,
    get_prompt,
    get_run,
    list_prompts,
    list_runs,
    update_run,
)

router = APIRouter(prefix="/api/v1")


# -- Health / Hello --

@router.get("/health")
async def health() -> dict:
    """Health check endpoint for load balancers and Docker health checks."""
    return {"status": "ok"}


@router.get("/hello")
async def hello() -> dict:
    """Hello world endpoint."""
    return {"message": "Mapping Business Resilience."}


# -- Documents --

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
    if file_path.resolve().parent != settings.upload_path.resolve():
        raise HTTPException(status_code=400, detail="Invalid filename")
    file_path.unlink()
    return {"deleted": filename}


# -- Prompts --

@router.get("/prompts")
async def list_prompts_endpoint() -> dict:
    prompts = await list_prompts()
    return {"prompts": prompts}


class PromptCreate(BaseModel):
    text: str


@router.post("/prompts", status_code=201)
async def create_prompt_endpoint(body: PromptCreate) -> dict:
    prompt = await create_prompt(body.text)
    return prompt


# -- Runs --

@router.get("/runs")
async def list_runs_endpoint(document_filename: str | None = None) -> dict:
    runs = await list_runs(document_filename)
    return {"runs": runs}


@router.get("/runs/{run_id}")
async def get_run_endpoint(run_id: str) -> dict:
    run = await get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


# -- Analyse --

class AnalyseRequest(BaseModel):
    prompt_id: str
    document_filename: str


@router.post("/analyse", status_code=201)
async def analyse_document(body: AnalyseRequest) -> dict:
    """Run LLM analysis on a document with a given prompt."""
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    prompt = await get_prompt(body.prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    file_path = settings.upload_path / body.document_filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document not found")

    run = await create_run(body.prompt_id, body.document_filename, settings.anthropic_model)

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        file_bytes = file_path.read_bytes()
        ext = file_path.suffix.lower()

        if ext == ".pdf":
            user_content = [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.b64encode(file_bytes).decode("ascii"),
                    },
                },
            ]
        else:
            text_content = file_bytes.decode("utf-8", errors="replace")
            user_content = [{"type": "text", "text": text_content}]

        start = time.monotonic()
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=8192,
            system=prompt["text"],
            messages=[{"role": "user", "content": user_content}],
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        output_text = response.content[0].text if response.content else ""

        await update_run(run["id"], status="complete", output=output_text, duration_ms=duration_ms)
        run["status"] = "complete"
        run["output"] = output_text
        run["duration_ms"] = duration_ms
        run["prompt_text"] = prompt["text"]

    except Exception as e:
        await update_run(run["id"], status="error", error_message=str(e))
        run["status"] = "error"
        run["error_message"] = str(e)
        run["prompt_text"] = prompt["text"]

    return run
