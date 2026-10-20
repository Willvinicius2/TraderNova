-- Testes de RLS da conta (Fase 2: #21, #22, #23). Independente de rls.sql: usuários e dados próprios.
\set ON_ERROR_STOP on
-- t.denied/t.rows vêm de supabase/tests/helpers.sql.

insert into auth.users values ('00000000-0000-4000-8000-0000000000c1'),('00000000-0000-4000-8000-0000000000c2');
set role service_role;
insert into public.research_signals(public_id,dedup_key,strategy_id,strategy_version,instrument,provider,timeframe_minutes,side,signal_time,generated_at,expires_at,entry_reference,stop,target,evidence,mode)
 values ('40000000-0000-4000-8000-0000000000c9','conta|teste','T1','E0X0','BTCUSD','kraken-spot',60,'buy',1,2,3,100,95,110,'[]','test');
insert into public.entitlements(user_id) values ('00000000-0000-4000-8000-0000000000c1'),('00000000-0000-4000-8000-0000000000c2');
reset role;

-- anon: nem preferências, nem exportação, nem exclusão.
set role anon;
select t.denied('anon lê preferências','select * from public.user_preferences');
select t.denied('anon exporta dados','select public.export_my_data()');
select t.denied('anon exclui conta','select public.delete_my_account()');
reset role;

-- Usuário C1: diário demo com retrato do sinal, sem informar user_id (padrão auth.uid()).
set role authenticated;
set request.jwt.claims='{"sub":"00000000-0000-4000-8000-0000000000c1"}';
insert into public.journal_entries(client_id,decision,note,mode,signal_snapshot,decided_at)
 values ('50000000-0000-4000-8000-0000000000c1','reviewed','nota','demo','{"id":"x","assetId":"BTCUSD"}',now());
select t.rows('C1 grava diário sem informar o dono',$q$select * from public.journal_entries where user_id='00000000-0000-4000-8000-0000000000c1'$q$,1);
-- Importação repetida não duplica (mesmo client_id).
insert into public.journal_entries(client_id,decision,mode,signal_snapshot,imported) values ('50000000-0000-4000-8000-0000000000c1','ignored','demo','{"id":"x"}',true) on conflict (user_id,client_id) do nothing;
select t.rows('importação idempotente','select * from public.journal_entries',1);
-- Registro de pesquisa pode apontar para o sinal persistido.
insert into public.journal_entries(client_id,decision,mode,signal_snapshot,research_signal_id) values ('50000000-0000-4000-8000-0000000000c2','reviewed','research','{"id":"y"}','40000000-0000-4000-8000-0000000000c9');
select t.denied('demo apontando para sinal real',$q$insert into public.journal_entries(client_id,decision,mode,signal_snapshot,research_signal_id) values (gen_random_uuid(),'reviewed','demo','{}','40000000-0000-4000-8000-0000000000c9')$q$,'23514');
select t.denied('diário sem sinal',$q$insert into public.journal_entries(client_id,decision,mode) values (gen_random_uuid(),'reviewed','research')$q$,'23514');
select t.denied('modo live no diário',$q$insert into public.journal_entries(client_id,decision,mode,signal_snapshot) values (gen_random_uuid(),'reviewed','live','{}')$q$,'23514');
select t.denied('C1 grava diário no nome de C2',$q$insert into public.journal_entries(user_id,client_id,decision,signal_snapshot) values ('00000000-0000-4000-8000-0000000000c2',gen_random_uuid(),'reviewed','{}')$q$);
insert into public.user_preferences(theme,density,alerts_in_app) values ('essential','compact',false);
insert into public.user_preferences(theme) values ('light') on conflict (user_id) do update set theme=excluded.theme;
select t.rows('C1 atualiza a própria preferência',$q$select * from public.user_preferences where theme='light'$q$,1);
select t.denied('tema inventado',$q$update public.user_preferences set theme='neon'$q$,'23514');
select t.denied('C1 grava preferência de C2',$q$insert into public.user_preferences(user_id,theme) values ('00000000-0000-4000-8000-0000000000c2','dark')$q$);
insert into public.push_devices(platform,device_reference,user_id) values ('android','aparelho-c1','00000000-0000-4000-8000-0000000000c1');
do $$ declare d jsonb := public.export_my_data(); begin
 if d->>'user_id'<>'00000000-0000-4000-8000-0000000000c1' then raise exception 'FALHOU exportação: usuário errado'; end if;
 if jsonb_array_length(d->'journal_entries')<>2 then raise exception 'FALHOU exportação: diário com % itens',jsonb_array_length(d->'journal_entries'); end if;
 if d->'user_preferences'->>'theme'<>'light' then raise exception 'FALHOU exportação: preferências'; end if;
 if jsonb_array_length(d->'push_devices')<>1 or d->'entitlements'->>'plan'<>'free' then raise exception 'FALHOU exportação: aparelhos/plano'; end if;
end $$;

-- C2 não vê nada de C1, nem pela exportação.
set request.jwt.claims='{"sub":"00000000-0000-4000-8000-0000000000c2"}';
select t.rows('C2 não vê diário de C1','select * from public.journal_entries',0);
select t.rows('C2 não vê preferências de C1','select * from public.user_preferences',0);
do $$ declare d jsonb := public.export_my_data(); begin
 if jsonb_array_length(d->'journal_entries')<>0 or jsonb_typeof(d->'user_preferences')<>'null' or jsonb_array_length(d->'push_devices')<>0 then raise exception 'FALHOU exportação de C2 vazou dados de C1'; end if;
end $$;
-- C2 apaga a própria conta: C1 continua intacto.
select public.delete_my_account();
-- Token sem sub não apaga ninguém.
set request.jwt.claims='{}';
select t.denied('exclusão sem sessão','select public.delete_my_account()');
select t.rows('sem sub não exporta',$q$select 1 where public.export_my_data() is not null$q$,0);

-- C1 apaga a própria conta: diário, preferências, aparelhos e plano somem em cascata.
set request.jwt.claims='{"sub":"00000000-0000-4000-8000-0000000000c1"}';
select public.delete_my_account();
reset role;
select t.rows('auth.users sem C1 e C2',$q$select * from auth.users where id in ('00000000-0000-4000-8000-0000000000c1','00000000-0000-4000-8000-0000000000c2')$q$,0);
select t.rows('diário de C1 apagado',$q$select * from public.journal_entries where user_id='00000000-0000-4000-8000-0000000000c1'$q$,0);
select t.rows('preferências de C1 apagadas',$q$select * from public.user_preferences where user_id='00000000-0000-4000-8000-0000000000c1'$q$,0);
select t.rows('aparelhos de C1 apagados',$q$select * from public.push_devices where user_id='00000000-0000-4000-8000-0000000000c1'$q$,0);
select t.rows('planos de C1 e C2 apagados',$q$select * from public.entitlements where user_id in ('00000000-0000-4000-8000-0000000000c1','00000000-0000-4000-8000-0000000000c2')$q$,0);
select t.rows('sinal de pesquisa preservado',$q$select * from public.research_signals where public_id='40000000-0000-4000-8000-0000000000c9'$q$,1);
-- Limpeza: não deixa linhas que mudem as contagens das outras suítes.
delete from public.research_signals where public_id='40000000-0000-4000-8000-0000000000c9';
select 'RLS conta: todos os testes passaram' as resultado;
