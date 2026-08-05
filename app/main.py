from contextlib import asynccontextmanager
from fastapi import FastAPI
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

# Automatic Column Auto-Migration on Startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # Create missing tables
        await conn.run_sync(Base.metadata.create_all)
        
        # Auto-inject missing columns into PostgreSQL DB table
        alter_queries = [
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 0 NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_priority VARCHAR(20) DEFAULT 'LOW' NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS seo_score INTEGER DEFAULT 0 NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_status VARCHAR(30) DEFAULT 'UNKNOWN' NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ssl_enabled BOOLEAN DEFAULT FALSE NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS mobile_friendly BOOLEAN DEFAULT FALSE NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS page_speed INTEGER DEFAULT 0 NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS meta_title TEXT;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS meta_description TEXT;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS robots_found BOOLEAN DEFAULT FALSE NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS sitemap_found BOOLEAN DEFAULT FALSE NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS schema_found BOOLEAN DEFAULT FALSE NOT NULL;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS domain_age INTEGER DEFAULT 0;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_summary TEXT;",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_audit_at TIMESTAMP WITH TIME ZONE;"
        ]
        
        for q in alter_queries:
            try:
                await conn.execute(text(q))
            except Exception as e:
                print(f"[Auto-Migration Log] {e}")
                
    yield


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
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
        "message": "Scrapely API is running 🚀",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "openapi": f"{settings.API_V1_STR}/openapi.json",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
    }
