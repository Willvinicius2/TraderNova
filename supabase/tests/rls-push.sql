-- Testes de RLS da migração de push (Fase 4). Usa t.* de helpers.sql; usuários e dados próprios (C/D), apagados no fim,
-- porque a ordem entre os rls*.sql não é garantida.
\set ON_ERROR_STOP on
insert into auth.users values ('00000000-0000-4000-8000-00000000000c'),('00000000-0000-4000-8000-00000000000d');
set role service_role;
insert into public.research_signals(public_id,dedup_key,strategy_id,strategy_version,instrument,provider,timeframe_minutes,side,signal_time,generated_at,expires_at,entry_reference,stop,evidence,mode)
 values ('50000000-0000-4000-8000-000000000001','push-test','T1','E0X0','BTCUSD','kraken-spot',60,'buy',1,2,3,100,95,'[]','test');
insert into public.push_devices(id,user_id,platform,device_reference) values
 ('60000000-0000-4000-8000-00000000000c','00000000-0000-4000-8000-00000000000c','android','ExponentPushToken[aaaaaaaaaaaa]'),
 ('60000000-0000-4000-8000-00000000000d','00000000-0000-4000-8000-00000000000d','ios','ExponentPushToken[bbbbbbbbbbbb]');
insert into public.push_deliveries(signal_public_id,device_id) values ('50000000-0000-4000-8000-000000000001','60000000-0000-4000-8000-00000000000c');
-- Dedup: o mesmo sinal no mesmo aparelho não entra duas vezes (23505 = unique).
select t.denied('entrega duplicada',$q$insert into public.push_deliveries(signal_public_id,device_id) values ('50000000-0000-4000-8000-000000000001','60000000-0000-4000-8000-00000000000c')$q$,'23505');
select t.denied('enviado sem ticket',$q$update public.push_deliveries set status='sent'$q$,'23514');
update public.push_deliveries set status='sent',ticket_id='t1';
select t.denied('token inválido no android',$q$insert into public.push_devices(user_id,platform,device_reference) values ('00000000-0000-4000-8000-00000000000c','android','qualquer-coisa')$q$,'23514');
select t.denied('ativo fora do catálogo',$q$insert into public.notification_preferences(user_id,muted_instruments) values ('00000000-0000-4000-8000-00000000000c','{DOGEUSD}')$q$,'23514');

-- Usuário C
set role authenticated;
set request.jwt.claims='{"sub":"00000000-0000-4000-8000-00000000000c"}';
insert into public.notification_preferences(user_id,enabled,include_research,muted_instruments) values ('00000000-0000-4000-8000-00000000000c',true,true,'{XAUUSD}');
select t.rows('C vê suas preferências','select * from public.notification_preferences',1);
select t.denied('C grava preferências de D',$q$insert into public.notification_preferences(user_id) values ('00000000-0000-4000-8000-00000000000d')$q$);
select t.denied('C lê entregas',$q$select * from public.push_deliveries$q$);
select t.denied('C forja entrega',$q$insert into public.push_deliveries(signal_public_id,device_id) values ('50000000-0000-4000-8000-000000000001','60000000-0000-4000-8000-00000000000d')$q$);
update public.push_devices set enabled=false,disabled_reason='desligado pelo usuário' where id='60000000-0000-4000-8000-00000000000c';
select t.rows('C desliga só o próprio aparelho',$q$select * from public.push_devices where not enabled$q$,1);
update public.push_devices set enabled=false where id='60000000-0000-4000-8000-00000000000d';

-- Usuário D não vê preferências nem aparelho de C.
set request.jwt.claims='{"sub":"00000000-0000-4000-8000-00000000000d"}';
select t.rows('D não vê preferências de C','select * from public.notification_preferences',0);
update public.notification_preferences set enabled=false;
select t.rows('D vê só o próprio aparelho','select * from public.push_devices',1);

-- anon: nada.
set role anon;
select t.denied('anon lê preferências',$q$select * from public.notification_preferences$q$);
select t.denied('anon lê aparelhos',$q$select * from public.push_devices$q$);
reset role;
select t.rows('aparelho de D continua ligado',$q$select * from public.push_devices where id='60000000-0000-4000-8000-00000000000d' and enabled$q$,1);
select t.rows('preferências de C intactas',$q$select * from public.notification_preferences where enabled$q$,1);
-- Apagar o sinal ou o aparelho apaga as entregas (sem órfãos).
delete from public.push_devices where id='60000000-0000-4000-8000-00000000000c';
select t.rows('entregas apagadas com o aparelho','select * from public.push_deliveries',0);
-- Limpeza: não deixa dados para os outros arquivos (apagar o usuário apaga aparelhos e preferências; o sinal leva as entregas).
delete from public.research_signals where public_id='50000000-0000-4000-8000-000000000001';
delete from auth.users where id in ('00000000-0000-4000-8000-00000000000c','00000000-0000-4000-8000-00000000000d');
select t.rows('limpeza completa',$q$select 1 from public.push_devices where device_reference like 'ExponentPushToken[%'$q$,0);
select 'RLS push: todos os testes passaram' as resultado;
