-- Run in your project's Supabase SQL editor.
create table if not exists public.patients (
    id text primary key,
    name text not null check (length(trim(name)) > 0),
    initials text not null,
    age integer check (age between 0 and 130),
    sex text not null default 'Not recorded',
    description text not null default 'Cloud patient workspace',
    created_at timestamptz not null default now()
);

alter table public.patients enable row level security;
-- Only the trusted Streamlit server writes. No public patient access policies.
revoke all on public.patients from anon, authenticated;
grant select, insert on public.patients to service_role;
