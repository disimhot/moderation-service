from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .api.router import router as api_router
from .api.service import classifier_service
from .config import settings

LOG_LEVEL = "debug" if settings.ENVIRONMENT == "dev" else "info"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML model on startup."""
    print("Loading classification model...")
    classifier_service.load()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Routers
app.include_router(api_router, tags=["Classification"])


@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME}",
        "version": settings.PROJECT_VERSION,
        "docs_url": "/docs",
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    return classifier_service.get_health_status()


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level=LOG_LEVEL)
