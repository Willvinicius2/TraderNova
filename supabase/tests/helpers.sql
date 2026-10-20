-- Funções de asserção dos testes de RLS (t.denied, t.rows). Carregado antes de todo supabase/tests/rls*.sql.
\set ON_ERROR_STOP on
create schema t;
grant usage on schema t to anon,authenticated,service_role;
-- Espera erro com o SQLSTATE dado (42501 = permissão/RLS, 23514 = check).
create function t.denied(label text,stmt text,code text default '42501') returns void language plpgsql as $$
begin
 begin execute stmt; exception when others then
  if sqlstate=code then return; end if;
  raise exception 'FALHOU %: esperado %, veio % (%)',label,code,sqlstate,sqlerrm;
 end;
 raise exception 'FALHOU %: deveria ter sido negado',label;
end $$;
create function t.rows(label text,stmt text,expected int) returns void language plpgsql as $$
declare n int; begin
 execute format('select count(*) from (%s) q',stmt) into n;
 if n<>expected then raise exception 'FALHOU %: esperado % linhas, veio %',label,expected,n; end if;
end $$;
grant execute on all functions in schema t to anon,authenticated,service_role;
