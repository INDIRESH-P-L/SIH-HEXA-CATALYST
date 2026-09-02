-- ═══════════════════════════════════════════════════════════════════════════
--  000 · LOCAL AUTH SHIM
--
--  Applied ONLY when AUTH_MODE=local. On Supabase this schema, this table and
--  this function are supplied by Supabase Auth (GoTrue) and the migration
--  runner skips this file.
--
--  Its whole purpose is so that 001_initial_schema.sql — which is the schema
--  from the build brief, unmodified — applies verbatim on plain Postgres:
--  every `references auth.users(id)` resolves, and every RLS policy that calls
--  auth.uid() compiles.
-- ═══════════════════════════════════════════════════════════════════════════

create extension if not exists "uuid-ossp";

create schema if not exists auth;

create table if not exists auth.users (
  id                 uuid primary key default uuid_generate_v4(),
  email              text unique not null,
  encrypted_password text not null,          -- PBKDF2-SHA256, stdlib hashlib
  created_at         timestamptz default now()
);

-- Mirrors Supabase's auth.uid(): the subject claim of the verified JWT, which
-- the connection sets with `set_config('request.jwt.claims', ...)`.
create or replace function auth.uid()
returns uuid
language sql
stable
as $$
  select nullif(
    current_setting('request.jwt.claims', true)::json ->> 'sub',
    ''
  )::uuid;
$$;
