-- public.rls_auto_enable() é a função do gatilho de evento do Supabase que liga RLS em toda tabela nova do schema public.
-- Ela só deve rodar como gatilho; ninguém da API precisa chamá-la por /rest/v1/rpc. Remove EXECUTE de public/anon/authenticated.
-- Em bancos sem essa função (teste local) não faz nada. Aplicada no projeto real em 21/10/2026 (aviso do advisor de segurança).
begin;
do $$ begin
 if exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='rls_auto_enable' and pg_get_function_identity_arguments(p.oid)='') then
  revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
 end if;
end $$;
commit;
