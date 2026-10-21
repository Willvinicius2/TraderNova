-- Fase 2: conta do usuário (issues #19, #21, #22, #23). Preparada; aplicar só no ambiente escolhido (ver docs/CONTA.md).
-- Diário sincronizado: journal_entries passa a aceitar as decisões do app (exemplos demo e sinais de pesquisa),
-- não só linhas de public.signals. Preferências por usuário. Exportação e exclusão da própria conta (LGPD).
begin;
-- O cliente nunca escolhe o dono da linha: o padrão é o usuário do token e a política continua exigindo auth.uid()=user_id.
alter table public.journal_entries alter column user_id set default auth.uid();
alter table public.journal_entries alter column signal_id drop not null;
alter table public.journal_entries
 add column client_id uuid,
 add column research_signal_id uuid references public.research_signals(public_id) on delete set null,
 add column signal_snapshot jsonb check(signal_snapshot is null or (jsonb_typeof(signal_snapshot)='object' and pg_column_size(signal_snapshot)<=4096)),
 add column mode text not null default 'demo' check(mode in ('demo','research')),
 add column decided_at timestamptz not null default now(),
 add column imported boolean not null default false;
-- client_id = ID gerado no aparelho: importar duas vezes o mesmo diário não duplica nada.
alter table public.journal_entries add constraint journal_entries_client_unique unique(user_id,client_id);
alter table public.journal_entries add constraint journal_entries_has_signal check(signal_id is not null or signal_snapshot is not null);
-- Exemplos sintéticos continuam marcados como demo: um registro demo nunca aponta para um sinal de pesquisa real.
alter table public.journal_entries add constraint journal_entries_demo_not_research check(mode<>'demo' or research_signal_id is null);

create table public.user_preferences (
 user_id uuid primary key default auth.uid() references auth.users(id) on delete cascade,
 theme text check(theme in ('essential','dark','light','system')),
 density text check(density in ('comfortable','compact')),
 alerts_in_app boolean not null default true,
 updated_at timestamptz not null default now()
);
alter table public.user_preferences enable row level security;
revoke all on public.user_preferences from anon,authenticated;
grant select,insert,update,delete on public.user_preferences to authenticated;
grant all on public.user_preferences to service_role;
create policy own_preferences on public.user_preferences for all to authenticated using((select auth.uid())=user_id) with check((select auth.uid())=user_id);

-- Exportação dos dados do próprio usuário. security invoker: as políticas de RLS decidem o que entra.
create function public.export_my_data() returns jsonb language sql stable security invoker set search_path='' as $$
 select jsonb_build_object(
  'user_id',auth.uid(),
  'exported_at',now(),
  'journal_entries',coalesce((select jsonb_agg(to_jsonb(j) order by j.decided_at desc) from public.journal_entries j),'[]'::jsonb),
  'user_preferences',(select to_jsonb(p) from public.user_preferences p),
  'push_devices',coalesce((select jsonb_agg(to_jsonb(d) order by d.created_at) from public.push_devices d),'[]'::jsonb),
  'entitlements',(select to_jsonb(e) from public.entitlements e)
 ) where auth.uid() is not null
$$;
revoke all on function public.export_my_data() from public,anon;
grant execute on function public.export_my_data() to authenticated;

-- Exclusão da própria conta. Apaga auth.users e, em cascata, diário, aparelhos, preferências, planos e demais linhas do usuário.
-- security definer só para alcançar auth.users; o alvo é sempre auth.uid() (nunca um parâmetro).
create function public.delete_my_account() returns void language plpgsql security definer set search_path='' as $$
declare uid uuid := auth.uid();
begin
 if uid is null then raise exception 'Sessão ausente' using errcode='42501'; end if;
 delete from auth.users where id=uid;
end $$;
revoke all on function public.delete_my_account() from public,anon;
grant execute on function public.delete_my_account() to authenticated;
create index journal_user_decided on public.journal_entries(user_id,decided_at desc);
commit;
