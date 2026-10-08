import React from 'react';
import { AlertTriangle } from 'lucide-react';

export interface SyntheticBannerProps {
  dataSource?: 'synthetic' | 'real';
  show?: boolean;
}

export const SyntheticBanner: React.FC<SyntheticBannerProps> = ({
  dataSource = 'synthetic',
  show,
}) => {
  const isVisible = show !== undefined ? show : dataSource === 'synthetic';
  if (!isVisible) return null;

  return (
    <div
      style={{
        background: 'linear-gradient(90deg, rgba(245, 158, 11, 0.18) 0%, rgba(217, 119, 6, 0.12) 100%)',
        borderBottom: '1px solid rgba(245, 158, 11, 0.35)',
        color: '#fbbf24',
        padding: '0.45rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.65rem',
        fontSize: '0.8rem',
        fontWeight: 600,
        letterSpacing: '0.02em',
      }}
    >
      <AlertTriangle size={15} style={{ flexShrink: 0, color: '#f59e0b' }} />
      <span>
        <strong>SYNTHETIC DEMO DATA:</strong> Model running in procedural mock mode. Detections and allometry are simulated for platform verification and not certified for regulatory carbon compliance.
      </span>
    </div>
  );
};
