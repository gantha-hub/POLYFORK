import React, { useState } from 'react';
import type { TabId } from './Sidebar';
import {
  Map,
  UploadCloud,
  Scale,
  CheckSquare,
  MoreHorizontal,
  GitCompare,
  Download,
  X,
} from 'lucide-react';

interface BottomNavProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, onTabChange }) => {
  const [isMoreOpen, setIsMoreOpen] = useState(false);

  const mainTabs: { id: TabId; label: string; icon: typeof Map }[] = [
    { id: 'map', label: 'Map', icon: Map },
    { id: 'surveys', label: 'Surveys', icon: UploadCloud },
    { id: 'calibration', label: 'Calibrate', icon: Scale },
    { id: 'verify', label: 'Audit', icon: CheckSquare },
  ];

  const handleSelectTab = (tab: TabId) => {
    onTabChange(tab);
    setIsMoreOpen(false);
  };

  const isMoreActive = activeTab === 'compare' || activeTab === 'export';

  return (
    <>
      {/* Mobile Bottom Navigation Bar */}
      <nav
        className="hide-on-desktop"
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: 'var(--bottom-nav-height)',
          background: 'rgba(9, 15, 12, 0.96)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          borderTop: '1px solid var(--border-card)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-around',
          padding: '0 0.5rem',
          zIndex: 1000,
          boxShadow: '0 -4px 20px rgba(0, 0, 0, 0.6)',
        }}
      >
        {mainTabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleSelectTab(tab.id)}
              className="touch-target"
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '3px',
                background: 'transparent',
                border: 'none',
                color: isActive ? 'var(--emerald-400)' : 'var(--text-muted)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
                padding: '4px 0',
              }}
            >
              <div
                style={{
                  padding: '3px 12px',
                  borderRadius: '12px',
                  background: isActive ? 'rgba(16, 185, 129, 0.16)' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
              </div>
              <span style={{ fontSize: '0.675rem', fontWeight: isActive ? 700 : 500 }}>
                {tab.label}
              </span>
            </button>
          );
        })}

        {/* More Options Tab */}
        <button
          onClick={() => setIsMoreOpen(true)}
          className="touch-target"
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
            background: 'transparent',
            border: 'none',
            color: isMoreActive ? 'var(--emerald-400)' : 'var(--text-muted)',
            cursor: 'pointer',
            padding: '4px 0',
          }}
        >
          <div
            style={{
              padding: '3px 12px',
              borderRadius: '12px',
              background: isMoreActive ? 'rgba(16, 185, 129, 0.16)' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <MoreHorizontal size={20} strokeWidth={isMoreActive ? 2.5 : 2} />
          </div>
          <span style={{ fontSize: '0.675rem', fontWeight: isMoreActive ? 700 : 500 }}>
            More
          </span>
        </button>
      </nav>

      {/* Touch Bottom Sheet for Secondary Actions (Compare, Export) */}
      {isMoreOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
            zIndex: 1100,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-end',
          }}
          onClick={() => setIsMoreOpen(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'rgba(12, 20, 16, 0.98)',
              borderTop: '1px solid var(--border-card)',
              borderTopLeftRadius: '20px',
              borderTopRightRadius: '20px',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
              paddingBottom: 'calc(1.5rem + env(safe-area-inset-bottom))',
            }}
          >
            {/* Handle & Close */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ width: 32, height: 4, borderRadius: 2, background: 'rgba(255,255,255,0.2)' }} />
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ffffff' }}>
                  Additional Observatory Tools
                </span>
              </div>
              <button
                onClick={() => setIsMoreOpen(false)}
                className="touch-target"
                style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: 'none',
                  borderRadius: '50%',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  width: 32,
                  height: 32,
                }}
              >
                <X size={16} />
              </button>
            </div>

            {/* Menu Items */}
            <button
              onClick={() => handleSelectTab('compare')}
              className="touch-target"
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '0.85rem',
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: activeTab === 'compare' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                border: '1px solid',
                borderColor: activeTab === 'compare' ? 'var(--emerald-500)' : 'var(--border-subtle)',
                color: activeTab === 'compare' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: '0.95rem',
                fontWeight: 600,
                textAlign: 'left',
              }}
            >
              <GitCompare size={20} color="var(--emerald-400)" />
              <div>
                <div>Temporal Evolution (T1 vs T2)</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400 }}>
                  Multi-flight change detection & tree mortality tracking
                </div>
              </div>
            </button>

            <button
              onClick={() => handleSelectTab('export')}
              className="touch-target"
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: '0.85rem',
                padding: '0.85rem 1rem',
                borderRadius: 'var(--radius-md)',
                background: activeTab === 'export' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.04)',
                border: '1px solid',
                borderColor: activeTab === 'export' ? 'var(--emerald-500)' : 'var(--border-subtle)',
                color: activeTab === 'export' ? '#ffffff' : 'var(--text-secondary)',
                fontSize: '0.95rem',
                fontWeight: 600,
                textAlign: 'left',
              }}
            >
              <Download size={20} color="var(--emerald-400)" />
              <div>
                <div>MRV Reports & Export</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 400 }}>
                  Download certified GeoJSON vectors, CSV inventory & PDFs
                </div>
              </div>
            </button>
          </div>
        </div>
      )}
    </>
  );
};
