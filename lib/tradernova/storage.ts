import {z} from 'zod';
const assetId=z.enum(['XAUUSD','NAS100','BTCUSD','ETHUSD','SOLUSD','EURUSD','USDJPY']);
const finite=z.number().finite();
const signal=z.object({id:z.string(),assetId,direction:z.enum(['Compra','Venda']),createdAt:finite,expiresAt:finite,entry:finite.positive(),stop:finite.positive(),target:finite.positive(),demo:z.literal(true),strategyId:z.string()});
const trade=z.object({entryTime:finite,exitTime:finite,direction:z.enum(['Compra','Venda']),entry:finite,exit:finite,r:finite,reason:z.string()});
export const demoStorage=z.object({version:z.literal(1),alertsOn:z.boolean(),signals:z.array(signal).max(30),journal:z.array(z.object({id:z.string(),signal,decision:z.enum(['Revisado','Ignorado']),createdAt:finite,note:z.string().max(500)})),report:z.object({id:z.string(),assetId:z.string(),createdAt:finite,source:z.literal('synthetic'),strategy:z.literal('BASELINE_EMA_CROSS_V1'),bars:finite,costR:finite,reward:finite,trades:z.array(trade),netR:finite,maxDrawdownR:finite,winRate:finite.nullable(),profitFactor:finite.nullable(),curve:z.array(finite).min(1)}).nullable()});
