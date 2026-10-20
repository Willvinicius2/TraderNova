-- Saúde do worker (heartbeat): uma linha por provedor/par/intervalo, regravada a cada ciclo (lib/tradernova/worker-status.ts).
-- Tempos em milissegundos desde a época, como em research_signals. Escrita só pelo service_role; leitura por authenticated e pelo servidor da web.
begin;
create table public.worker_status (
 provider text not null check(length(provider) between 1 and 40),
 instrument text not null check(length(instrument) between 1 and 20),
 timeframe_minutes integer not null check(timeframe_minutes>0),
 poll_seconds integer not null check(poll_seconds between 5 and 600),
 last_cycle_at bigint not null check(last_cycle_at>=0),
 last_success_at bigint check(last_success_at is null or last_success_at>=0),
 feed_state text not null check(feed_state in ('ao_vivo','atrasado','desconectado','historico_insuficiente')),
 last_closed_open_time bigint check(last_closed_open_time is null or last_closed_open_time>=0),
 updated_at timestamptz not null default now(),
 primary key(provider,instrument,timeframe_minutes)
);
alter table public.worker_status enable row level security;
revoke all on public.worker_status from anon,authenticated;
grant select on public.worker_status to authenticated;
grant all on public.worker_status to service_role;
create policy read_worker_status on public.worker_status for select to authenticated using(true);
commit;
