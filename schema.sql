-- WhoGapsWho vehicle catalog schema.
-- Run via scripts/seed_db.py, or manually with:
--   psql -d whogapswho -f schema.sql

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('car', 'motorbike')),
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    engine TEXT NOT NULL,
    horsepower NUMERIC NOT NULL,
    torque NUMERIC NOT NULL,
    zero_to_sixty NUMERIC NOT NULL,
    top_speed NUMERIC NOT NULL,
    weight NUMERIC NOT NULL,
    price NUMERIC,
    drivetrain TEXT,
    body_style TEXT,
    bike_style TEXT
);

-- Trigram index so "search as you type" on make/model/year stays fast
-- once this holds thousands of rows instead of dozens.
CREATE INDEX IF NOT EXISTS vehicles_search_trgm_idx
    ON vehicles USING gin ((make || ' ' || model || ' ' || year::text) gin_trgm_ops);
