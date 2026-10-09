import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import type {
  ProjectResponse,
  SurveyResponse,
  HealthResponse,
  CalibrationStatusResponse,
} from '../types/api';

interface ProjectContextType {
  health: HealthResponse | null;
  projects: ProjectResponse[];
  activeProject: ProjectResponse | null;
  surveys: SurveyResponse[];
  activeSurvey: SurveyResponse | null;
  calibrationStatus: CalibrationStatusResponse | null;
  calibration: CalibrationStatusResponse | null;
  dataSource: 'synthetic' | 'real';
  loading: boolean;
  setActiveProject: (project: ProjectResponse | null) => void;
  setActiveSurvey: (survey: SurveyResponse | null) => void;
  refreshProjects: () => Promise<void>;
  refreshSurveys: () => Promise<void>;
  refreshCalibration: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [activeProject, setActiveProject] = useState<ProjectResponse | null>(null);
  const [surveys, setSurveys] = useState<SurveyResponse[]>([]);
  const [activeSurvey, setActiveSurvey] = useState<SurveyResponse | null>(null);
  const [calibrationStatus, setCalibrationStatus] = useState<CalibrationStatusResponse | null>(null);
  const [dataSource, setDataSource] = useState<'synthetic' | 'real'>('synthetic');
  const [loading, setLoading] = useState<boolean>(true);

  // Check health and load projects on initial mount
  useEffect(() => {
    async function init() {
      try {
        const hRes = await api.getHealth();
        setHealth(hRes.data);
        setDataSource(hRes.data_source);
      } catch (err) {
        console.warn('Backend offline or health check failed:', err);
      }

      try {
        const pRes = await api.getProjects();
        setProjects(pRes.data);
        if (pRes.data.length > 0) {
          // Smart select: locate the project with real surveys first
          let projectWithSurveys = pRes.data[0];
          for (const proj of pRes.data) {
            try {
              const sRes = await api.getProjectSurveys(proj.id);
              if (sRes.data && sRes.data.length > 0) {
                projectWithSurveys = proj;
                setSurveys(sRes.data);
                setActiveSurvey(sRes.data[0]);
                break;
              }
            } catch {
              // try next project
            }
          }
          setActiveProject(projectWithSurveys);
        }
      } catch (err) {
        console.error('Failed to load projects:', err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // Fetch surveys and calibration status whenever active project changes
  const refreshSurveys = useCallback(async () => {
    if (!activeProject) {
      setSurveys([]);
      setActiveSurvey(null);
      return;
    }
    try {
      const sRes = await api.getProjectSurveys(activeProject.id);
      setSurveys(sRes.data);
      if (sRes.data.length > 0) {
        // Keep current survey if it belongs to this project, otherwise select first
        setActiveSurvey((prev) => {
          const match = sRes.data.find((s) => s.id === prev?.id);
          return match || sRes.data[0];
        });
      } else {
        setActiveSurvey(null);
      }
    } catch (err) {
      console.warn('Failed to load surveys for project:', err);
      setSurveys([]);
      setActiveSurvey(null);
    }
  }, [activeProject]);

  const refreshCalibration = useCallback(async () => {
    if (!activeProject) {
      setCalibrationStatus(null);
      return;
    }
    try {
      const cRes = await api.getCalibrationStatus(activeProject.id);
      setCalibrationStatus(cRes.data);
    } catch (err) {
      console.warn('Failed to load calibration status:', err);
      setCalibrationStatus(null);
    }
  }, [activeProject]);

  useEffect(() => {
    refreshSurveys();
    refreshCalibration();
  }, [activeProject, refreshSurveys, refreshCalibration]);

  const refreshProjects = async () => {
    try {
      const pRes = await api.getProjects();
      setProjects(pRes.data);
      if (!activeProject && pRes.data.length > 0) {
        setActiveProject(pRes.data[0]);
      }
    } catch (err) {
      console.error('Failed to refresh projects:', err);
    }
  };

  return (
    <ProjectContext.Provider
      value={{
        health,
        projects,
        activeProject,
        surveys,
        activeSurvey,
        calibrationStatus,
        calibration: calibrationStatus,
        dataSource,
        loading,
        setActiveProject,
        setActiveSurvey,
        refreshProjects,
        refreshSurveys,
        refreshCalibration,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = (): ProjectContextType => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
};
