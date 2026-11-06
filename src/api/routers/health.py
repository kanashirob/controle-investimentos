from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Saúde"])


@router.get("/health")
def health_check():
    return {"status": "ok"}
