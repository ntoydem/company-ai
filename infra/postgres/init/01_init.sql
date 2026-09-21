-- Runs once when the Postgres data directory is first initialised.
-- Executed by psql as POSTGRES_USER (superuser) inside POSTGRES_DB.
CREATE EXTENSION IF NOT EXISTS vector;

-- Separate database for automated tests (SPEC_06 §9).
CREATE DATABASE company_ai_test;
\connect company_ai_test
CREATE EXTENSION IF NOT EXISTS vector;
