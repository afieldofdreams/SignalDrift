import uuid
from datetime import datetime, UTC
from pathlib import Path

import aiosqlite

from app.config import settings

DEFAULT_PROMPT = """\
You are a sustainability analyst. You are extracting a claim map from a single ESG report.

Goals
- Identify the most decision-relevant claims in the report
- For each claim, capture verbatim evidence and where it appears
- Make the evidence easy to locate and highlight in a PDF viewer

Rules
- Only use information that is explicitly present in the document
- Do not infer, assume, or add external context
- Every claim must include verbatim evidence quotes copied exactly from the report
- Every claim must include page numbers for each quote
- Prefer evidence that is easy to match using PDF text search
  - Choose short exact excerpts that appear as continuous text in the report
  - Avoid breaking lines mid sentence where possible
  - Avoid tables unless the table text is clearly extractable
- If you cannot find strong verbatim evidence for a claim, do not include the claim

What counts as a claim
A claim is a concrete statement the company is making about performance, targets, governance, policy, controls, programmes, or coverage. Examples include targets, reductions, coverage statements, audit statements, supplier assessments, risk governance, water stewardship actions, biodiversity plans.

Output format
Return a JSON object only, with the following structure and constraints.

Top level fields
- document_title string
- reporting_year string or null
- company_name string or null
- claims array

Claim object fields
- id string, short stable identifier like C001
- theme string, one of
  - Governance and oversight
  - Targets and commitments
  - Metrics and performance
  - Risk management
  - Value chain and suppliers
  - Water and nature
  - People and workforce
  - Other
- claim_text string, a single sentence paraphrase of the claim in neutral language
- claim_type string, one of
  - metric
  - target
  - governance
  - policy
  - programme
  - coverage
  - narrative
- evidence array, 1 to 3 items

Evidence object fields
- quote string, verbatim text copied exactly from the report
- page_number integer, 1-based
- locator string, a short exact substring from the quote, 20 to 80 characters, that is likely to be unique on the page and can be used for highlighting
- notes string or null, only if needed to explain why matching might be difficult, for example hyphenation or line breaks

Quality thresholds
- Provide 12 to 25 claims maximum
- Prefer high-signal claims that an analyst would cite
- Avoid generic statements like we care about the environment unless paired with a specific policy, metric, target, or programme

Now extract the claim map from the attached document."""


def _db_path() -> str:
    p = Path(settings.db_path)
    path = p if p.is_absolute() else Path(settings.upload_path).parent / p
    return str(path)


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(_db_path())
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db() -> None:
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                prompt_id TEXT NOT NULL REFERENCES prompts(id),
                document_filename TEXT NOT NULL,
                model TEXT NOT NULL,
                output TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                duration_ms INTEGER,
                created_at TEXT NOT NULL
            );
        """)
        cursor = await db.execute("SELECT COUNT(*) FROM prompts")
        row = await cursor.fetchone()
        if row[0] == 0:
            await db.execute(
                "INSERT INTO prompts (id, text, created_at) VALUES (?, ?, ?)",
                (_new_id(), DEFAULT_PROMPT, _now()),
            )
        await db.commit()
    finally:
        await db.close()


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> str:
    return datetime.now(UTC).isoformat()


# -- Prompt CRUD --

async def list_prompts() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, text, created_at FROM prompts ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def get_prompt(prompt_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, text, created_at FROM prompts WHERE id = ?", (prompt_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def create_prompt(text: str) -> dict:
    prompt = {"id": _new_id(), "text": text, "created_at": _now()}
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO prompts (id, text, created_at) VALUES (?, ?, ?)",
            (prompt["id"], prompt["text"], prompt["created_at"]),
        )
        await db.commit()
        return prompt
    finally:
        await db.close()


# -- Run CRUD --

async def create_run(prompt_id: str, document_filename: str, model: str) -> dict:
    run = {
        "id": _new_id(),
        "prompt_id": prompt_id,
        "document_filename": document_filename,
        "model": model,
        "output": None,
        "status": "pending",
        "error_message": None,
        "duration_ms": None,
        "created_at": _now(),
    }
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO runs (id, prompt_id, document_filename, model, output, status, error_message, duration_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run["id"], run["prompt_id"], run["document_filename"], run["model"],
             run["output"], run["status"], run["error_message"], run["duration_ms"], run["created_at"]),
        )
        await db.commit()
        return run
    finally:
        await db.close()


async def update_run(run_id: str, *, status: str, output: str | None = None,
                     error_message: str | None = None, duration_ms: int | None = None) -> None:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE runs SET status = ?, output = ?, error_message = ?, duration_ms = ? WHERE id = ?",
            (status, output, error_message, duration_ms, run_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_run(run_id: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT r.*, p.text as prompt_text
               FROM runs r JOIN prompts p ON r.prompt_id = p.id
               WHERE r.id = ?""",
            (run_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def list_runs(document_filename: str | None = None) -> list[dict]:
    db = await get_db()
    try:
        if document_filename:
            cursor = await db.execute(
                """SELECT r.*, p.text as prompt_text
                   FROM runs r JOIN prompts p ON r.prompt_id = p.id
                   WHERE r.document_filename = ?
                   ORDER BY r.created_at DESC""",
                (document_filename,),
            )
        else:
            cursor = await db.execute(
                """SELECT r.*, p.text as prompt_text
                   FROM runs r JOIN prompts p ON r.prompt_id = p.id
                   ORDER BY r.created_at DESC""",
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()
