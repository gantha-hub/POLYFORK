import React from 'react';
import type { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { BottomNav } from './BottomNav';
import type { TabId } from './Sidebar';
import { SyntheticBanner } from '../common/SyntheticBanner';

interface AppShellProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  isSynthetic: boolean;
  children: ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  activeTab,
  onTabChange,
  isSynthetic,
  children,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        background: 'var(--bg-app)',
        overflow: 'hidden',
      }}
    >
      {/* Top Application Bar */}
      <Header />

      {/* Synthetic Demo Warning Banner */}
      <SyntheticBanner show={isSynthetic} />

      {/* Main Workspace Body */}
      <div
        style={{
          display: 'flex',
          flex: 1,
          height: 'calc(100vh - var(--header-height, 58px))',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <Sidebar activeTab={activeTab} onTabChange={onTabChange} />

        <main
          style={{
            flex: 1,
            height: '100%',
            overflowY: 'auto',
            background: 'var(--bg-app)',
            position: 'relative',
            paddingBottom: 'calc(var(--bottom-nav-height, 64px) * var(--is-mobile, 0))',
          }}
        >
          {children}
        </main>
      </div>

      {/* Touch-Friendly Mobile Bottom Navigation */}
      <BottomNav activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
};
