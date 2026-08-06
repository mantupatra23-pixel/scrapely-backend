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
    # Initialize base metadata schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-Migration Pipeline
    migration_queries = [
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'emailstatusenum') THEN CREATE TYPE emailstatusenum AS ENUM ('VALID', 'VERIFIED', 'INVALID', 'RISKY', 'NOT_FOUND'); END IF; END $$;",
        "ALTER TABLE leads ALTER COLUMN source SET DEFAULT 'GOOGLE_MAPS';",
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'leadpriorityenum') THEN CREATE TYPE leadpriorityenum AS ENUM ('HIGH', 'MEDIUM', 'LOW'); END IF; END $$;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS workspace_id UUID;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone_formatted VARCHAR(100);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS phone_country_code VARCHAR(10);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS verified_email VARCHAR(255);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS email_source VARCHAR(100);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS state VARCHAR(255);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS postal_code VARCHAR(50);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS latitude FLOAT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS longitude FLOAT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS google_rating FLOAT DEFAULT 0.0;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS business_status VARCHAR(100) DEFAULT 'OPERATIONAL';",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS opening_hours JSONB;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS primary_category VARCHAR(255);",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS google_maps_url TEXT;",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS seo_audit_details JSONB;",
        "ALTER TABLE leads ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;"
    ]

    for query in migration_queries:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(query))
        except Exception:
            pass

    # Clear old legacy/hardcoded test leads from PostgreSQL
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM leads WHERE google_place_id LIKE 'yelp_%' OR google_place_id LIKE 'osm_%' OR google_place_id LIKE 'custom_%' OR company_name LIKE '%Dentists in%';"))
    except Exception:
        pass

    yield


app = FastAPI(
    title="Scrapely.ai Enterprise Lead Engine",
    openapi_url="/api/v1/openapi.json",
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
        "application": "Scrapely.ai Live Enterprise",
        "status": "healthy",
    }
