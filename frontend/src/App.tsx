import React, { useState } from 'react';
import { ProjectProvider, useProject } from './context/ProjectContext';
import { AppShell } from './components/layout/AppShell';
import type { TabId } from './components/layout/Sidebar';
import { MapPage } from './pages/MapPage';
import { SurveysPage } from './pages/SurveysPage';
import { CalibrationPage } from './pages/CalibrationPage';
import { ComparePage } from './pages/ComparePage';
import { VerifyPage } from './pages/VerifyPage';
import { ExportPage } from './pages/ExportPage';

const AppContent: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('map');
  const { activeSurvey, health } = useProject();

  // Show synthetic warning banner if model backend is mock or filename indicates demo
  const isSynthetic =
    health?.model_backend === 'mock' ||
    (activeSurvey?.original_filename?.toLowerCase().includes('synthetic') ?? false) ||
    (activeSurvey?.original_filename?.toLowerCase().includes('demo') ?? false);

  return (
    <AppShell
      activeTab={activeTab}
      onTabChange={setActiveTab}
      isSynthetic={Boolean(isSynthetic)}
    >
      {activeTab === 'map' && (
        <MapPage onNavigateToSurveys={() => setActiveTab('surveys')} />
      )}
      {activeTab === 'surveys' && (
        <SurveysPage onNavigateToMap={() => setActiveTab('map')} />
      )}
      {activeTab === 'calibration' && <CalibrationPage />}
      {activeTab === 'compare' && <ComparePage />}
      {activeTab === 'verify' && <VerifyPage />}
      {activeTab === 'export' && <ExportPage />}
    </AppShell>
  );
};

export default function App() {
  return (
    <ProjectProvider>
      <AppContent />
    </ProjectProvider>
  );
}
