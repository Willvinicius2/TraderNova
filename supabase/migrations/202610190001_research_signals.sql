-- Sinais de pesquisa gravados pelo worker, espelhando o contrato SignalRecord (lib/tradernova/signal-record.ts).
-- Tempos em milissegundos desde a época (bigint), como no contrato. Ver docs/SINAIS.md.
-- Escrita só pelo service_role (worker). Leitura: authenticated (Fase 2, RLS por usuário) e o servidor da web com chave de servidor.
-- anon não lê nada: o ID público é opaco e não concede acesso por si só.
begin;
create table public.research_signals (
 public_id uuid primary key,
 dedup_key text not null unique check(length(dedup_key) between 1 and 300),
 strategy_id text not null check(length(strategy_id) between 1 and 40),
 strategy_version text not null check(length(strategy_version) between 1 and 40),
 instrument text not null check(length(instrument) between 1 and 20),
 provider text not null check(length(provider) between 1 and 40),
 timeframe_minutes integer not null check(timeframe_minutes>0),
 side text not null check(side in ('buy','sell')),
 signal_time bigint not null check(signal_time>=0),
 generated_at bigint not null check(generated_at>=0),
 expires_at bigint not null check(expires_at>generated_at),
 entry_reference numeric not null check(entry_reference>0),
 stop numeric not null check(stop>0),
 target numeric check(target is null or target>0),
 evidence jsonb not null default '[]' check(jsonb_typeof(evidence)='array' and jsonb_array_length(evidence)<=20),
 mode text not null check(mode in ('research','test','alert')),
 invalidated_at bigint check(invalidated_at is null or invalidated_at>=0),
 invalidation_reason text check(invalidation_reason is null or length(invalidation_reason)<=300),
 created_at timestamptz not null default now(),
 check((side='buy' and stop<entry_reference and (target is null or target>entry_reference))
    or (side='sell' and stop>entry_reference and (target is null or target<entry_reference)))
);
alter table public.research_signals enable row level security;
revoke all on public.research_signals from anon,authenticated;
grant select on public.research_signals to authenticated;
grant all on public.research_signals to service_role;
-- Sinais de pesquisa não pertencem a um usuário: qualquer conta autenticada pode ler. Escrita não tem política (só service_role, que ignora RLS).
create policy read_research_signals on public.research_signals for select to authenticated using(true);
create index research_signals_recent on public.research_signals(instrument,timeframe_minutes,signal_time desc);
commit;
