import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.settings import settings
from app.db.session import engine, Base
from app.models import Lead
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
    # 1. Base table structure initialization
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Dynamic Auto-Migration Queries for Enterprise Schema Alignment
    alter_queries = [
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS workspace_id UUID;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone_formatted VARCHAR(100);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone_country_code VARCHAR(10);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_mobile BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS has_whatsapp BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS verified_email VARCHAR(255);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_source VARCHAR(100);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_syntax_valid BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_mx_valid BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_smtp_valid BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_is_disposable BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_is_catch_all BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_is_role_based BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS state VARCHAR(255);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS postal_code VARCHAR(50);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS latitude FLOAT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS longitude FLOAT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS google_rating FLOAT DEFAULT 0.0;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS business_status VARCHAR(100) DEFAULT 'OPERATIONAL';",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS opening_hours JSONB;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS primary_category VARCHAR(255);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS secondary_categories JSONB;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS google_maps_url TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS directions_url TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS photos_url TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS business_description TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS seo_audit_details JSONB;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS tech_stack JSONB;",
        "ALTER TABLE leads ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;"
    ]

    for q in alter_queries:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(q))
        except Exception as e:
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
        "message": "Scrapely Enterprise Engine is running 🚀",
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "timestamp": time.time(),
    }
