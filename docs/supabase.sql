-- Run in the Supabase SQL editor before using the authenticated app.
-- Transactional and safe to re-run. Historical rows keep NULL owners and stay hidden.
begin;
create table if not exists public.patients (
    id text not null,
    name text not null check (length(trim(name)) > 0),
    initials text not null,
    age integer check (age between 0 and 130),
    sex text not null default 'Not recorded',
    description text not null default 'Cloud patient workspace',
    created_at timestamptz not null default now()
);
alter table public.patients add column if not exists owner_id uuid references auth.users(id);
alter table public.patients alter column owner_id set default auth.uid();
-- A separate primary key allows legacy unassigned rows to remain hidden and
-- different users to use the same patient ID without collisions.
alter table public.patients add column if not exists row_id uuid not null default gen_random_uuid();
alter table public.patients drop constraint if exists patients_pkey;
alter table public.patients add constraint patients_pkey primary key (row_id);
alter table public.patients alter column id set not null;
create unique index if not exists patients_owner_patient_id on public.patients(owner_id, id);
alter table public.patients enable row level security;
revoke all on public.patients from anon, authenticated;
grant select, insert on public.patients to authenticated;
grant select, insert on public.patients to service_role;
-- The restrictive policy prevents older permissive policies widening ownership.
drop policy if exists patients_owner_guard on public.patients;
create policy patients_owner_guard on public.patients as restrictive for all to authenticated
    using ((select auth.uid()) = owner_id)
    with check ((select auth.uid()) = owner_id);
drop policy if exists patients_select_own on public.patients;
create policy patients_select_own on public.patients for select to authenticated
    using ((select auth.uid()) = owner_id);
drop policy if exists patients_insert_own on public.patients;
create policy patients_insert_own on public.patients for insert to authenticated
    with check ((select auth.uid()) = owner_id);
commit;
-- Assign historical records ONLY after verifying who owns them, for example:
-- update public.patients set owner_id = '<verified-auth-user-uuid>'
-- where row_id = '<specific-patient-row-uuid>' and owner_id is null;
-- Legacy Pinecone patient-<id> records are intentionally not read by this app.
-- Re-upload reports under the verified owner's account to migrate safely.
