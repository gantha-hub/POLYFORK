import React from 'react';

export type BadgeType =
  | 'calibrated'
  | 'uncalibrated'
  | 'synthetic'
  | 'real'
  | 'status'
  | 'danger'
  | 'default'
  | 'custom';

export interface BadgeProps {
  type?: BadgeType;
  variant?: BadgeType;
  label: string;
  color?: string;
  bgColor?: string;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  type,
  variant,
  label,
  color,
  bgColor,
  icon,
}) => {
  const activeType = variant || type || 'default';
  let className = 'badge';

  if (activeType === 'calibrated') className += ' badge-calibrated';
  else if (activeType === 'uncalibrated') className += ' badge-uncalibrated';
  else if (activeType === 'synthetic') className += ' badge-synthetic';
  else if (activeType === 'real') className += ' badge-real';
  else if (activeType === 'danger') {
    className += ' font-mono';
    bgColor = bgColor || 'rgba(239, 68, 68, 0.15)';
    color = color || '#f87171';
  } else {
    className += ' font-mono';
    bgColor = bgColor || 'rgba(255, 255, 255, 0.06)';
    color = color || 'var(--text-secondary)';
  }

  const customStyle: React.CSSProperties = {};
  if (color) customStyle.color = color;
  if (bgColor) customStyle.backgroundColor = bgColor;

  return (
    <span className={className} style={customStyle}>
      {icon && <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>}
      {label}
    </span>
  );
};
