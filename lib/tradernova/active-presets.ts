// Generated from the frozen development selection and validation adoption rule.
import type {StrategyParameters} from './calibration';
import type {CandidateId} from './research';
export const activePresets:Record<CandidateId,StrategyParameters>={
  "T1": {
    "id": "T1-E0X0",
    "candidateId": "T1",
    "entryProfile": "original",
    "stopAtr": 1.5,
    "hold": 8,
    "reward": 2,
    "trendFilter": false,
    "minStopFraction": 0
  },
  "T2": {
    "id": "T2-E0X2",
    "candidateId": "T2",
    "entryProfile": "original",
    "stopAtr": 3,
    "hold": 72,
    "reward": 3,
    "trendFilter": false,
    "minStopFraction": 0
  },
  "T3": {
    "id": "T3-E1X2",
    "candidateId": "T3",
    "entryProfile": "trend-cost",
    "stopAtr": 3,
    "hold": 72,
    "reward": 3,
    "trendFilter": true,
    "minStopFraction": 0.0072
  }
};
