import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.settings import settings
from app.db.session import engine, Base
from app.api.v1 import (
    auth,
    leads,
    billing,
    api_keys,
    exports,
    intelligence,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Base tables initialization
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Safe isolated column auto-injections
    alter_queries = [
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS country VARCHAR(100) DEFAULT 'United States';",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS city VARCHAR(255) DEFAULT 'New York';",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS google_place_id VARCHAR(255);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 85;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_priority VARCHAR(50) DEFAULT 'HIGH';",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS seo_score INTEGER DEFAULT 80;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_status VARCHAR(50) DEFAULT 'VERIFIED';",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS rating FLOAT DEFAULT 4.5;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS reviews_count INTEGER DEFAULT 30;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS source VARCHAR(100) DEFAULT 'live_swarm';",
        "ALTER TABLE leads ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;"
    ]

    for q in alter_queries:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(q))
        except Exception:
            pass

    yield


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response


app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(leads.router, prefix=settings.API_V1_STR)
app.include_router(billing.router, prefix=settings.API_V1_STR)
app.include_router(api_keys.router, prefix=settings.API_V1_STR)
app.include_router(exports.router, prefix=settings.API_V1_STR)
app.include_router(intelligence.router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
async def root():
    return {
        "success": True,
        "application": settings.APP_NAME,
        "message": "Scrapely API Engine is running 🚀",
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "timestamp": time.time(),
    }
