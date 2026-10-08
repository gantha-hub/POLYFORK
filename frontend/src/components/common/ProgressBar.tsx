import React from 'react';

interface ProgressBarProps {
  progress: number; // 0 to 100
  status?: string;
  error?: string | null;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress, status = 'processing', error }) => {
  const isFailed = status === 'failed';
  const isCompleted = status === 'completed';

  const barColor = isFailed ? '#ef4444' : isCompleted ? '#10b981' : 'linear-gradient(90deg, #10b981, #34d399)';

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: 600 }}>
        <span style={{ color: isFailed ? '#ef4444' : 'var(--text-secondary)', textTransform: 'capitalize' }}>
          {isFailed ? `Failed: ${error || 'Unknown error'}` : isCompleted ? 'Completed (100%)' : `Status: ${status}...`}
        </span>
        <span className="font-mono" style={{ color: 'var(--emerald-400)' }}>
          {progress}%
        </span>
      </div>
      <div
        style={{
          width: '100%',
          height: 8,
          background: 'rgba(255, 255, 255, 0.08)',
          borderRadius: 'var(--radius-pill)',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <div
          style={{
            width: `${Math.min(100, Math.max(0, progress))}%`,
            height: '100%',
            background: barColor,
            borderRadius: 'var(--radius-pill)',
            transition: 'width 0.4s ease-out',
            boxShadow: isCompleted ? '0 0 10px rgba(16, 185, 129, 0.5)' : undefined,
          }}
        />
      </div>
    </div>
  );
};
