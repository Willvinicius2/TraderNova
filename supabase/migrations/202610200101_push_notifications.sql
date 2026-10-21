-- Fase 4: notificações push (issues #33-#35). Regras em lib/tradernova/push-notifications.ts; ver docs/NOTIFICACOES.md.
-- push_devices já existe (base). Aqui: token Expo validado, desligamento pelo servidor, preferências e registro de entregas (dedup).
begin;
alter table public.push_devices
 add column enabled boolean not null default true,
 add column disabled_reason text check(disabled_reason is null or length(disabled_reason)<=200),
 add column updated_at timestamptz not null default now(),
 -- Em android/ios a referência é o token do Expo Push (ExponentPushToken[...]); nunca credencial de corretora.
 add constraint push_devices_expo_token check(platform='web' or device_reference ~ '^Expo(nent)?PushToken\[[A-Za-z0-9_-]{10,200}\]$');
create index push_devices_enabled on public.push_devices(user_id) where enabled;

-- Preferências por usuário. Padrão desligado: notificação de pesquisa só com opt-in explícito.
create table public.notification_preferences (
 user_id uuid primary key references auth.users(id) on delete cascade,
 enabled boolean not null default false,
 include_research boolean not null default false,
 muted_instruments text[] not null default '{}' check(muted_instruments <@ array['XAUUSD','NAS100','BTCUSD','ETHUSD','SOLUSD','EURUSD','USDJPY']::text[]),
 muted_strategies text[] not null default '{}' check(cardinality(muted_strategies)<=50 and array_position(muted_strategies,null) is null),
 updated_at timestamptz not null default now()
);
alter table public.notification_preferences enable row level security;
revoke all on public.notification_preferences from anon,authenticated;
grant select,insert,update,delete on public.notification_preferences to authenticated;
grant all on public.notification_preferences to service_role;
create policy own_notification_preferences on public.notification_preferences for all to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id);

-- Uma linha por (sinal, dispositivo). A chave primária é o claim: quem não consegue inserir não envia (no máximo uma notificação).
-- Só o servidor (service_role) lê e escreve.
create table public.push_deliveries (
 signal_public_id uuid not null references public.research_signals(public_id) on delete cascade,
 device_id uuid not null references public.push_devices(id) on delete cascade,
 status text not null default 'claimed' check(status in ('claimed','sent','failed')),
 ticket_id text check(ticket_id is null or length(ticket_id)<=200),
 error text check(error is null or length(error)<=200),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 primary key(signal_public_id,device_id),
 check(status<>'sent' or ticket_id is not null)
);
alter table public.push_deliveries enable row level security;
revoke all on public.push_deliveries from anon,authenticated;
grant all on public.push_deliveries to service_role;
create index push_deliveries_device on public.push_deliveries(device_id);
commit;
