from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }