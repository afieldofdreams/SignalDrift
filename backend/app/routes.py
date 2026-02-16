from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/health")
async def health() -> dict:
    """Health check endpoint for load balancers and Docker health checks."""
    return {"status": "ok"}


@router.get("/hello")
async def hello() -> dict:
    """Hello world endpoint."""
    return {"message": "Hello, World!"}
