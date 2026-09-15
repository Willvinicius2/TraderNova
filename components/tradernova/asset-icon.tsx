import { BarChart3 } from 'lucide-react';
import type { AssetId } from '@/lib/tradernova/domain';
import './asset-icon.css';

const artwork = {
  XAUUSD: '/assets/instruments/gold.svg',
  BTCUSD: '/assets/instruments/bitcoin.svg',
  ETHUSD: '/assets/instruments/ethereum.svg',
  SOLUSD: '/assets/instruments/solana.svg',
} as const;

/** Decorative identifier: the adjacent instrument name supplies its accessible label. */
export function AssetIcon({ id, size = 36, className = '' }: {
  id: AssetId;
  size?: 24 | 32 | 36 | 44;
  className?: string;
}) {
  const pair = id === 'EURUSD' ? ['eu', 'us'] : id === 'USDJPY' ? ['us', 'jp'] : null;
  return (
    <span
      aria-hidden="true"
      className={`asset-emblem asset-emblem--${id.toLowerCase()} ${className}`}
      style={{ width: size, height: size }}
    >
      {id === 'XAUUSD' ? (
        <span className="asset-emblem__bullion" />
      ) : pair ? (
        <span className="asset-emblem__pair">
          {pair.map((country, index) => (
            <img key={country} className={`asset-emblem__flag asset-emblem__flag--${index}`}
              src={`/assets/instruments/${country}.svg`} alt="" width={24} height={24}
              draggable={false} decoding="async" />
          ))}
        </span>
      ) : id === 'NAS100' ? (
        <BarChart3 className="asset-emblem__index" aria-hidden="true" strokeWidth={2.2} />
      ) : id in artwork ? (
        <img className="asset-emblem__image" src={artwork[id as keyof typeof artwork]} alt="" width={size} height={size}
          draggable={false} decoding="async" />
      ) : null}
    </span>
  );
}
