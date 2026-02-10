import uvicorn
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


from .api.router import router as api_router
from .config import settings

LOG_LEVEL = "debug" if settings.ENVIRONMENT == "dev" else "info"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(2.0),
    )
    yield
    await app.state.http_client.aclose()


# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# --- Routers ---
app.include_router(
    api_router, prefix=f"{settings.API_V1_STR}/classification", tags=["Classification"]
)

# --- Middleware ---
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """Root endpoint providing basic API information."""
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API",
        "version": settings.PROJECT_VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
    }


# --- Health Check Endpoint ---
@app.get("/health", tags=["Health Check"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.PROJECT_VERSION}


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level=LOG_LEVEL)
