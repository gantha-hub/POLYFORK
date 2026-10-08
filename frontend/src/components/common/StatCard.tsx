import React from 'react';
import { Badge } from './Badge';

interface StatCardProps {
  title: string;
  value: string | number;
  unit?: string;
  interval?: { low: number; high: number; confidenceLevel?: number };
  intervalLabel?: string;
  calibrated?: boolean;
  subtitle?: string;
  icon?: React.ReactNode;
  accentColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  unit,
  interval,
  intervalLabel = '90% prediction interval',
  calibrated,
  subtitle,
  icon,
  accentColor = 'var(--emerald-500)',
}) => {
  return (
    <div
      className="glass-card"
      style={{
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.65rem',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.02em' }}>
          {title}
        </span>
        {icon && (
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-md)',
              background: 'rgba(255, 255, 255, 0.05)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: accentColor,
            }}
          >
            {icon}
          </div>
        )}
      </div>

      {/* Main Metric Value */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginTop: '0.15rem' }}>
        <span style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          {value}
        </span>
        {unit && (
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            {unit}
          </span>
        )}
      </div>

      {/* Statistical Interval & Calibration Tag */}
      {interval && (
        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.1rem' }}>
          <span
            className="font-mono"
            style={{
              fontSize: '0.785rem',
              fontWeight: 600,
              color: 'var(--text-emerald)',
              background: 'rgba(16, 185, 129, 0.1)',
              padding: '0.15rem 0.5rem',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(16, 185, 129, 0.2)',
            }}
          >
            [{interval.low.toLocaleString()} — {interval.high.toLocaleString()}]
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            {intervalLabel}
          </span>
        </div>
      )}

      {/* Footer Details */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '0.4rem' }}>
        {subtitle && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {subtitle}
          </span>
        )}
        {calibrated !== undefined && (
          <Badge
            type={calibrated ? 'calibrated' : 'uncalibrated'}
            label={calibrated ? 'Calibrated' : 'Uncalibrated'}
          />
        )}
      </div>
    </div>
  );
};
