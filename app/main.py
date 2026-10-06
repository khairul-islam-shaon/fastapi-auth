from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.app_env,
    }