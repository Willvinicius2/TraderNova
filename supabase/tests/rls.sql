-- Testes de RLS das migrações (issue #13). Rodar com scripts/test-rls.mjs. Cada falha aborta com mensagem clara.
\set ON_ERROR_STOP on

-- Dados: dois usuários, cada um com sua estratégia, instrumento e sinal (inseridos como service_role).
insert into auth.users values ('00000000-0000-4000-8000-00000000000a'),('00000000-0000-4000-8000-00000000000b');
set role service_role;
insert into public.instrument_profiles(id,user_id,display_symbol,provider,broker_symbol,server,contract_type,volume_type,tick_size,currency) values
 ('10000000-0000-4000-8000-00000000000a','00000000-0000-4000-8000-00000000000a','BTCUSD','kraken','XBTUSD','spot','spot','traded',0.1,'USD'),
 ('10000000-0000-4000-8000-00000000000b','00000000-0000-4000-8000-00000000000b','BTCUSD','kraken','XBTUSD','spot','spot','traded',0.1,'USD');
insert into public.strategy_versions(id,user_id,name,version) values
 ('20000000-0000-4000-8000-00000000000a','00000000-0000-4000-8000-00000000000a','T1','1'),
 ('20000000-0000-4000-8000-00000000000b','00000000-0000-4000-8000-00000000000b','T1','1');
insert into public.signals(id,user_id,strategy_version_id,instrument_id,direction,entry,stop,target,generated_at,expires_at,status,mode,source,evidence) values
 ('30000000-0000-4000-8000-00000000000a','00000000-0000-4000-8000-00000000000a','20000000-0000-4000-8000-00000000000a','10000000-0000-4000-8000-00000000000a','buy',100,95,110,now(),now()+interval '1 hour','observation','demo','teste','[]'),
 ('30000000-0000-4000-8000-00000000000b','00000000-0000-4000-8000-00000000000b','20000000-0000-4000-8000-00000000000b','10000000-0000-4000-8000-00000000000b','buy',100,95,110,now(),now()+interval '1 hour','observation','demo','teste','[]');
insert into public.entitlements(user_id) values ('00000000-0000-4000-8000-00000000000a'),('00000000-0000-4000-8000-00000000000b');
insert into public.research_signals(public_id,dedup_key,strategy_id,strategy_version,instrument,provider,timeframe_minutes,side,signal_time,generated_at,expires_at,entry_reference,stop,target,evidence,mode)
 values ('40000000-0000-4000-8000-000000000001','T1|E0X0|kraken-spot|BTCUSD|60|buy|1','T1','E0X0','BTCUSD','kraken-spot',60,'buy',1,2,3,100,95,110,'["teste"]','test');
-- Worker: duplicata pela chave de deduplicação é ignorada (on conflict), incoerência de preços é rejeitada.
insert into public.research_signals(public_id,dedup_key,strategy_id,strategy_version,instrument,provider,timeframe_minutes,side,signal_time,generated_at,expires_at,entry_reference,stop,target,evidence,mode)
 values ('40000000-0000-4000-8000-000000000002','T1|E0X0|kraken-spot|BTCUSD|60|buy|1','T1','E0X0','BTCUSD','kraken-spot',60,'buy',1,2,3,100,95,110,'[]','test') on conflict (dedup_key) do nothing;
insert into public.worker_status(provider,instrument,timeframe_minutes,poll_seconds,last_cycle_at,feed_state) values ('kraken-spot','BTCUSD',60,30,1,'ao_vivo');
insert into public.worker_status(provider,instrument,timeframe_minutes,poll_seconds,last_cycle_at,feed_state) values ('kraken-spot','BTCUSD',60,30,2,'atrasado')
 on conflict (provider,instrument,timeframe_minutes) do update set last_cycle_at=excluded.last_cycle_at,feed_state=excluded.feed_state;
select t.rows('heartbeat sobrescreve a mesma linha',$q$select * from public.worker_status where last_cycle_at=2$q$,1);
select t.denied('estado de feed inventado',$q$insert into public.worker_status(provider,instrument,timeframe_minutes,poll_seconds,last_cycle_at,feed_state) values ('k','ETHUSD',60,30,1,'otimo')$q$,'23514');
select t.rows('dedup no banco','select * from public.research_signals',1);
select t.denied('stop acima da entrada numa compra',$q$insert into public.research_signals(public_id,dedup_key,strategy_id,strategy_version,instrument,provider,timeframe_minutes,side,signal_time,generated_at,expires_at,entry_reference,stop,evidence,mode) values (gen_random_uuid(),'x','T1','E0X0','BTCUSD','k',60,'buy',1,2,3,100,105,'[]','test')$q$,'23514');
select t.denied('modo fora da lista',$q$insert into public.research_signals(public_id,dedup_key,strategy_id,strategy_version,instrument,provider,timeframe_minutes,side,signal_time,generated_at,expires_at,entry_reference,stop,evidence,mode) values (gen_random_uuid(),'y','T1','E0X0','BTCUSD','k',60,'buy',1,2,3,100,95,'[]','live')$q$,'23514');
reset role;

-- anon: nada.
set role anon;
select t.denied('anon lê '||tbl,'select * from public.'||tbl) from unnest(array['instrument_profiles','strategy_versions','test_runs','signals','journal_entries','entitlements','push_devices','research_signals','worker_status']) tbl;
select t.denied('anon grava research_signals',$q$delete from public.research_signals$q$);
reset role;

-- Usuário A: vê só o que é seu; não se promove; não grava no nome de B.
set role authenticated;
set request.jwt.claims='{"sub":"00000000-0000-4000-8000-00000000000a"}';
select t.rows('A vê seu sinal','select * from public.signals',1);
select t.rows('A não vê sinal de B',$q$select * from public.signals where user_id='00000000-0000-4000-8000-00000000000b'$q$,0);
select t.rows('A vê só sua estratégia','select * from public.strategy_versions',1);
select t.rows('A vê só seu instrumento','select * from public.instrument_profiles',1);
select t.rows('A vê só seu plano','select * from public.entitlements',1);
select t.denied('A se dá Pro',$q$update public.entitlements set plan='pro',status='active',expires_at=now()+interval '1 year'$q$);
select t.denied('A cria plano',$q$insert into public.entitlements(user_id,plan) values ('00000000-0000-4000-8000-00000000000a','pro')$q$);
select t.denied('A valida estratégia',$q$update public.strategy_versions set status='validated',validation_evidence='{}'$q$);
select t.denied('A cria sinal',$q$insert into public.signals(user_id,strategy_version_id,instrument_id,direction,entry,stop,target,generated_at,expires_at,status,mode,source,evidence) values ('00000000-0000-4000-8000-00000000000a','20000000-0000-4000-8000-00000000000a','10000000-0000-4000-8000-00000000000a','buy',100,95,110,now(),now()+interval '1 hour','eligible','live','x','[]')$q$);
select t.denied('A grava diário no nome de B',$q$insert into public.journal_entries(user_id,signal_id,decision) values ('00000000-0000-4000-8000-00000000000b','30000000-0000-4000-8000-00000000000b','reviewed')$q$);
insert into public.journal_entries(user_id,signal_id,decision) values ('00000000-0000-4000-8000-00000000000a','30000000-0000-4000-8000-00000000000a','reviewed');
select t.rows('A vê seu diário','select * from public.journal_entries',1);
insert into public.push_devices(user_id,platform,device_reference) values ('00000000-0000-4000-8000-00000000000a','web','dispositivo-a');
select t.denied('A registra aparelho de B',$q$insert into public.push_devices(user_id,platform,device_reference) values ('00000000-0000-4000-8000-00000000000b','web','x')$q$);
select t.rows('A lê sinais de pesquisa','select * from public.research_signals',1);
select t.denied('A grava sinal de pesquisa',$q$insert into public.research_signals(public_id,dedup_key,strategy_id,strategy_version,instrument,provider,timeframe_minutes,side,signal_time,generated_at,expires_at,entry_reference,stop,evidence,mode) values (gen_random_uuid(),'z','T1','E0X0','BTCUSD','k',60,'buy',1,2,3,100,95,'[]','test')$q$);
select t.denied('A altera sinal de pesquisa',$q$update public.research_signals set stop=1$q$);
select t.denied('A apaga sinal de pesquisa',$q$delete from public.research_signals$q$);
select t.rows('A lê a saúde do worker','select * from public.worker_status',1);
select t.denied('A altera a saúde do worker',$q$update public.worker_status set feed_state='ao_vivo'$q$);

-- Usuário B não vê o diário nem o aparelho de A.
set request.jwt.claims='{"sub":"00000000-0000-4000-8000-00000000000b"}';
select t.rows('B não vê diário de A','select * from public.journal_entries',0);
select t.rows('B não vê aparelho de A','select * from public.push_devices',0);
delete from public.journal_entries;

-- Sem usuário (token sem sub): nada do que é por usuário.
set request.jwt.claims='{}';
select t.rows('sem sub não vê sinais','select * from public.signals',0);
select t.rows('sem sub não vê planos','select * from public.entitlements',0);
reset role;
select t.rows('diário de A sobreviveu ao delete de B','select * from public.journal_entries',1);
select 'RLS: todos os testes passaram' as resultado;
