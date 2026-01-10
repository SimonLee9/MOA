-- MOA Database Initialization
-- ============================
-- This script runs when PostgreSQL container starts for the first time

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For Korean text search

-- Set timezone
SET timezone = 'Asia/Seoul';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE moa TO moa;

-- Note: Tables are created by SQLAlchemy ORM
-- This file is for any additional setup needed before the app runs
