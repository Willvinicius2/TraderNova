-- TraderNova foundation. Prepared only; not applied to a Supabase project.
-- Credentials, billing verification, market jobs and push delivery remain server-side.
begin;
create table public.instrument_profiles (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 display_symbol text not null, provider text not null, broker_symbol text not null, server text not null,
 contract_type text not null check(contract_type in ('spot','cfd','future','forex','index')),
 volume_type text not null check(volume_type in ('traded','ticks','unavailable')),
 tick_size numeric not null check(tick_size>0), currency text not null,
 created_at timestamptz not null default now(), unique(id,user_id)
);
create table public.strategy_versions (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 name text not null, version text not null, parameters jsonb not null default '{}',
 status text not null default 'specified' check(status in ('specified','testing','rejected','validated')),
 validation_evidence jsonb, created_at timestamptz not null default now(), unique(id,user_id),
 check(status <> 'validated' or validation_evidence is not null)
);
create table public.test_runs (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 strategy_version_id uuid not null, instrument_id uuid not null,
 source text not null check(source in ('synthetic','historical','forward')),
 status text not null default 'queued' check(status in ('queued','running','completed','failed')),
 range_start timestamptz not null, range_end timestamptz not null, cost_model jsonb not null,
 metrics jsonb, data_hash text, engine_version text not null,
 created_at timestamptz not null default now(), unique(id,user_id), check(range_end>range_start),
 foreign key(strategy_version_id,user_id) references public.strategy_versions(id,user_id),
 foreign key(instrument_id,user_id) references public.instrument_profiles(id,user_id)
);
create table public.signals (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 strategy_version_id uuid not null, instrument_id uuid not null,
 direction text not null check(direction in ('buy','sell')), entry numeric not null check(entry>0),
 stop numeric not null check(stop>0), target numeric not null check(target>0),
 generated_at timestamptz not null, expires_at timestamptz not null,
 status text not null check(status in ('observation','eligible','expired','invalidated','conflict','unavailable')),
 mode text not null check(mode in ('demo','paper','live')), source text not null, evidence jsonb not null,
 unique(id,user_id), check(expires_at>generated_at), check(mode<>'demo' or status<>'eligible'),
 check((direction='buy' and stop<entry and target>entry) or (direction='sell' and target<entry and stop>entry)),
 foreign key(strategy_version_id,user_id) references public.strategy_versions(id,user_id),
 foreign key(instrument_id,user_id) references public.instrument_profiles(id,user_id)
);
create table public.journal_entries (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 signal_id uuid not null, decision text not null check(decision in ('reviewed','ignored','manually_executed')),
 actual_entry numeric, actual_exit numeric, note text check(length(note)<=2000),
 created_at timestamptz not null default now(), unique(user_id,signal_id),
 foreign key(signal_id,user_id) references public.signals(id,user_id)
);
create table public.entitlements (
 user_id uuid primary key references auth.users(id) on delete cascade,
 plan text not null default 'free' check(plan in ('free','pro')), status text not null default 'inactive' check(status in ('inactive','active','expired')),
 provider text check(provider in ('apple','google','web')), expires_at timestamptz, updated_at timestamptz not null default now(),
 check(plan<>'pro' or status<>'active' or expires_at is not null)
);
create table public.push_devices (
 id uuid primary key default gen_random_uuid(), user_id uuid not null references auth.users(id) on delete cascade,
 platform text not null check(platform in ('web','android','ios')), device_reference text not null,
 created_at timestamptz not null default now(), unique(user_id,device_reference)
);
-- Server-owned tables have SELECT only; users cannot promote a strategy or grant Pro.
alter table public.instrument_profiles enable row level security;
alter table public.strategy_versions enable row level security;
alter table public.test_runs enable row level security;
alter table public.signals enable row level security;
alter table public.journal_entries enable row level security;
alter table public.entitlements enable row level security;
alter table public.push_devices enable row level security;
revoke all on public.instrument_profiles,public.strategy_versions,public.test_runs,public.signals,public.journal_entries,public.entitlements,public.push_devices from anon,authenticated;
grant select on public.instrument_profiles,public.strategy_versions,public.test_runs,public.signals,public.entitlements to authenticated;
grant select,insert,update,delete on public.journal_entries,public.push_devices to authenticated;
grant all on public.instrument_profiles,public.strategy_versions,public.test_runs,public.signals,public.journal_entries,public.entitlements,public.push_devices to service_role;
create policy own_instruments on public.instrument_profiles for select to authenticated using((select auth.uid())=user_id);
create policy own_strategies on public.strategy_versions for select to authenticated using((select auth.uid())=user_id);
create policy own_runs on public.test_runs for select to authenticated using((select auth.uid())=user_id);
create policy own_signals on public.signals for select to authenticated using((select auth.uid())=user_id);
create policy own_entitlements on public.entitlements for select to authenticated using((select auth.uid())=user_id);
create policy own_journal on public.journal_entries for all to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id);
create policy own_devices on public.push_devices for all to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id);
create index signals_user_expiry on public.signals(user_id,expires_at desc);
create index journal_user_date on public.journal_entries(user_id,created_at desc);
create index runs_user_date on public.test_runs(user_id,created_at desc);
create index strategies_user on public.strategy_versions(user_id);
create index instruments_user on public.instrument_profiles(user_id);
commit;
