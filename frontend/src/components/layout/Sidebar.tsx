import React from 'react';
import { useProject } from '../../context/ProjectContext';
import { Badge } from '../common/Badge';
import {
  Map,
  UploadCloud,
  Scale,
  GitCompare,
  CheckSquare,
  Download,
  BookOpen,
  Trees,
} from 'lucide-react';

import type { LucideIcon } from 'lucide-react';

export type TabId = 'map' | 'surveys' | 'calibration' | 'compare' | 'verify' | 'export';

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  const { activeProject, surveys, calibration } = useProject();

  const navItems: { id: TabId; label: string; icon: LucideIcon }[] = [
    { id: 'map', label: 'Digital Twin Map', icon: Map },
    { id: 'surveys', label: 'Surveys & Ingestion', icon: UploadCloud },
    { id: 'calibration', label: 'Ground Calibration', icon: Scale },
    { id: 'compare', label: 'Temporal Evolution', icon: GitCompare },
    { id: 'verify', label: 'Active Audit Queue', icon: CheckSquare },
    { id: 'export', label: 'MRV Reports & Export', icon: Download },
  ];

  return (
    <aside
      className="hide-on-mobile"
      style={{
        width: 250,
        minWidth: 250,
        height: '100%',
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '1.25rem 0.85rem',
      }}
    >
      {/* Navigation Links */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
        <div
          style={{
            fontSize: '0.675rem',
            fontWeight: 700,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            padding: '0 0.75rem 0.5rem',
          }}
        >
          Observatory Views
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                width: '100%',
                padding: '0.65rem 0.85rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid',
                borderColor: isActive ? 'var(--border-focus)' : 'transparent',
                background: isActive ? 'rgba(16, 185, 129, 0.12)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.85rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all var(--transition-fast)',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  e.currentTarget.style.color = '#ffffff';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
            >
              <Icon
                size={18}
                className={isActive ? undefined : undefined}
                style={{
                  color: isActive ? 'var(--emerald-400)' : 'var(--text-muted)',
                  transition: 'color var(--transition-fast)',
                }}
              />
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.id === 'surveys' && surveys.length > 0 && (
                <span
                  className="font-mono"
                  style={{
                    fontSize: '0.7rem',
                    background: 'rgba(255, 255, 255, 0.06)',
                    color: 'var(--text-secondary)',
                    padding: '0.1rem 0.4rem',
                    borderRadius: 'var(--radius-pill)',
                  }}
                >
                  {surveys.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Stand Metadata & Status Footer */}
      <div
        className="glass-card"
        style={{
          padding: '0.85rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          background: 'rgba(9, 15, 12, 0.95)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Trees size={15} color="var(--emerald-400)" />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              Stand Status
            </span>
          </div>
          <Badge
            variant={calibration?.calibrated ? 'calibrated' : 'uncalibrated'}
            label={calibration?.calibrated ? 'Calibrated' : 'Uncalibrated'}
          />
        </div>

        <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>Project: </strong>
            {activeProject?.name || 'None selected'}
          </div>
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>Surveys: </strong>
            {surveys.length} registered
          </div>
        </div>

        {/* API Docs Link */}
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            fontSize: '0.725rem',
            color: 'var(--text-muted)',
            paddingTop: '0.4rem',
            borderTop: '1px solid var(--border-subtle)',
          }}
        >
          <BookOpen size={13} />
          <span>Interactive OpenAPI Docs</span>
        </a>
      </div>
    </aside>
  );
};
