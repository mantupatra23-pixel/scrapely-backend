-- Scrapely.ai Enterprise PostgreSQL Relational Database Schema
-- Location: app/db/schema.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enum Declarations
CREATE TYPE user_role AS ENUM ('SUPER_ADMIN', 'ADMIN', 'AGENCY_OWNER', 'MEMBER');
CREATE TYPE job_status AS ENUM ('QUEUED', 'LAUNCHING_BROWSER', 'SEARCHING', 'COLLECTING', 'VERIFYING_EMAILS', 'RUNNING_AI', 'RUNNING_SEO', 'EXPORTING', 'COMPLETED', 'FAILED', 'CANCELLED');
CREATE TYPE lead_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'URGENT');
CREATE TYPE email_status AS ENUM ('VERIFIED', 'INVALID', 'RISKY', 'CATCH_ALL', 'UNKNOWN');
CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'PAST_DUE', 'CANCELED', 'UNPAID', 'TRIALING');

-- 1. Workspaces Table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    logo_url TEXT,
    timezone VARCHAR(100) DEFAULT 'UTC',
    default_country VARCHAR(100) DEFAULT 'United States',
    default_export_format VARCHAR(20) DEFAULT 'csv',
    credits_balance INTEGER DEFAULT 500 NOT NULL,
    auto_recharge BOOLEAN DEFAULT FALSE,
    auto_recharge_threshold INTEGER DEFAULT 50,
    auto_recharge_amount INTEGER DEFAULT 500,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    avatar_url TEXT,
    role user_role DEFAULT 'AGENCY_OWNER',
    is_email_verified BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    company VARCHAR(255),
    website TEXT,
    linkedin_url TEXT,
    bio TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Authentication Sessions & Login History
CREATE TABLE IF NOT EXISTS active_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    device_name VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Scrape Jobs Table
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    city VARCHAR(255) NOT NULL,
    state VARCHAR(255),
    country VARCHAR(100) NOT NULL,
    radius_km INTEGER DEFAULT 10,
    zip_code VARCHAR(30),
    status job_status DEFAULT 'QUEUED',
    target_limit INTEGER DEFAULT 20,
    found_count INTEGER DEFAULT 0,
    duplicates_count INTEGER DEFAULT 0,
    verified_emails_count INTEGER DEFAULT 0,
    error_message TEXT,
    execution_time_sec NUMERIC(10,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Leads Table
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    job_id UUID REFERENCES scrape_jobs(id) ON DELETE SET NULL,
    google_place_id VARCHAR(255) UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    website TEXT,
    phone VARCHAR(100),
    email VARCHAR(255),
    email_status email_status DEFAULT 'UNKNOWN',
    email_risk_score INTEGER DEFAULT 0,
    address TEXT,
    city VARCHAR(255) NOT NULL,
    state VARCHAR(255),
    country VARCHAR(100) NOT NULL,
    zip_code VARCHAR(30),
    category VARCHAR(255),
    employee_count VARCHAR(50),
    revenue_estimate VARCHAR(100),
    google_rating NUMERIC(3,2) DEFAULT 0.00,
    reviews_count INTEGER DEFAULT 0,
    linkedin_url TEXT,
    instagram_url TEXT,
    facebook_url TEXT,
    twitter_url TEXT,
    lead_score INTEGER DEFAULT 0,
    seo_score INTEGER DEFAULT 0,
    lead_priority lead_priority DEFAULT 'LOW',
    buying_intent VARCHAR(50) DEFAULT 'MODERATE',
    decision_maker_prob VARCHAR(50) DEFAULT 'MEDIUM',
    ai_reasons JSONB DEFAULT '[]'::jsonb,
    ai_suggestions JSONB DEFAULT '[]'::jsonb,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. SEO Audits Table
CREATE TABLE IF NOT EXISTS seo_audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID UNIQUE NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    ssl_enabled BOOLEAN DEFAULT FALSE,
    https_redirect BOOLEAN DEFAULT FALSE,
    page_speed_ms INTEGER DEFAULT 0,
    mobile_friendly BOOLEAN DEFAULT FALSE,
    meta_title TEXT,
    meta_description TEXT,
    canonical_found BOOLEAN DEFAULT FALSE,
    schema_found BOOLEAN DEFAULT FALSE,
    robots_found BOOLEAN DEFAULT FALSE,
    sitemap_found BOOLEAN DEFAULT FALSE,
    google_business_claimed BOOLEAN DEFAULT FALSE,
    core_web_vitals_score INTEGER DEFAULT 0,
    broken_links_count INTEGER DEFAULT 0,
    open_graph_valid BOOLEAN DEFAULT FALSE,
    twitter_card_valid BOOLEAN DEFAULT FALSE,
    raw_issues JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Cold Email Templates & Generated Outbox
CREATE TABLE IF NOT EXISTS email_outreach (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    subject TEXT NOT NULL,
    body_content TEXT NOT NULL,
    cta_text TEXT,
    followup_1 TEXT,
    followup_2 TEXT,
    followup_3 TEXT,
    tone VARCHAR(50) DEFAULT 'Professional',
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. API Keys Table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    webhook_secret VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '["leads:read", "leads:write"]'::jsonb,
    requests_count INTEGER DEFAULT 0,
    is_revoked BOOLEAN DEFAULT FALSE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Billing & Invoices Table
CREATE TABLE IF NOT EXISTS billing_invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    stripe_invoice_id VARCHAR(255),
    amount_paid NUMERIC(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    credits_added INTEGER DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    invoice_pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Database Performance Indexes
CREATE INDEX IF NOT EXISTS idx_leads_workspace_location ON leads (workspace_id, country, city, category);
CREATE INDEX IF NOT EXISTS idx_leads_search_trgm ON leads USING gin (company_name gin_trgm_ops, category gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_workspace_status ON scrape_jobs (workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_active_sessions_user ON active_sessions (user_id, is_active);
