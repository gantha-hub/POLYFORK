/**
 * Type-safe API client for VrikshaVision backend.
 * Includes automated fallback to realistic demo dataset when deployed statically (e.g. GitHub Pages).
 */

import type {
  ResponseEnvelope,
  HealthResponse,
  ProjectResponse,
  ProjectCreate,
  SurveyResponse,
  JobResponse,
  SurveyResultsSummary,
  CalibrationFitRequest,
  CalibrationStatusResponse,
  SurveyComparisonResponse,
  TreeQueueItem,
  VerificationCreate,
  VerificationResponse,
} from '../types/api';

import {
  DEMO_HEALTH,
  DEMO_PROJECTS,
  DEMO_SURVEYS,
  DEMO_RESULTS,
  DEMO_CALIBRATION,
  DEMO_COMPARISON,
  DEMO_VERIFY_QUEUE,
} from './demoData';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

/**
 * Standard fetch wrapper that unwraps ResponseEnvelope,
 * with seamless fallback to offline demo data on static hosts.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ResponseEnvelope<T>> {
  const url = `${API_BASE}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.ok) {
      return await response.json();
    }
  } catch {
    // Network failure (e.g. GitHub Pages static hosting with no local backend)
  }

  // Graceful fallback for static deployments (GitHub Pages)
  const fallbackData = getStaticFallback<T>(endpoint, options);
  if (fallbackData !== null) {
    return {
      success: true,
      data: fallbackData,
      error: null,
      data_source: 'synthetic',
    };
  }

  throw new Error(`Unable to reach backend at ${endpoint}`);
}

function getStaticFallback<T>(endpoint: string, options: RequestInit): T | null {
  if (endpoint.startsWith('/health')) {
    return DEMO_HEALTH as unknown as T;
  }
  if (endpoint.startsWith('/projects') && !endpoint.includes('/surveys')) {
    if (options.method === 'POST') {
      const newProj: ProjectResponse = {
        id: `proj-${Date.now()}`,
        name: 'Custom Forestry Project',
        description: 'Created during live interactive demo',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      return newProj as unknown as T;
    }
    return DEMO_PROJECTS as unknown as T;
  }
  if (endpoint.includes('/surveys')) {
    return DEMO_SURVEYS as unknown as T;
  }
  if (endpoint.startsWith('/results')) {
    return DEMO_RESULTS as unknown as T;
  }
  if (endpoint.startsWith('/calibration/status')) {
    return DEMO_CALIBRATION as unknown as T;
  }
  if (endpoint.startsWith('/calibration/fit')) {
    return DEMO_CALIBRATION as unknown as T;
  }
  if (endpoint.startsWith('/calibration/plots')) {
    return { project_id: 'demo-stand-01', imported_plots: 14 } as unknown as T;
  }
  if (endpoint.startsWith('/compare')) {
    return DEMO_COMPARISON as unknown as T;
  }
  if (endpoint.startsWith('/verify/queue')) {
    return DEMO_VERIFY_QUEUE as unknown as T;
  }
  if (endpoint.startsWith('/verify') && options.method === 'POST') {
    return {
      id: `ver-${Date.now()}`,
      tree_id: 'TREE-AUDITED',
      action: 'accept',
      user_id: 'forester_auditor',
      notes: 'Audited in live demo session',
      timestamp: new Date().toISOString(),
    } as unknown as T;
  }
  if (endpoint.startsWith('/upload')) {
    return DEMO_SURVEYS[0] as unknown as T;
  }
  if (endpoint.startsWith('/jobs')) {
    const job: JobResponse = {
      id: `job-${Date.now()}`,
      survey_id: 'survey-demo-2026',
      job_type: 'canopy_segmentation_allometry',
      status: 'completed',
      progress: 1.0,
      error: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return job as unknown as T;
  }

  return null;
}

export const api = {
  // System Health
  getHealth: () => apiRequest<HealthResponse>('/health'),

  // Projects
  getProjects: (skip = 0, limit = 50) =>
    apiRequest<ProjectResponse[]>(`/projects?skip=${skip}&limit=${limit}`),
  
  getProject: (projectId: string) =>
    apiRequest<ProjectResponse>(`/projects/${projectId}`),

  createProject: (payload: ProjectCreate) =>
    apiRequest<ProjectResponse>('/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getProjectSurveys: (projectId: string) =>
    apiRequest<SurveyResponse[]>(`/projects/${projectId}/surveys`),

  // Upload & Surveys
  uploadRaster: (formData: FormData) =>
    apiRequest<SurveyResponse>('/upload', {
      method: 'POST',
      body: formData,
    }),

  // Jobs
  startJob: (surveyId: string) =>
    apiRequest<JobResponse>('/jobs', {
      method: 'POST',
      body: JSON.stringify({ survey_id: surveyId }),
    }),

  getJobStatus: (jobId: string) =>
    apiRequest<JobResponse>(`/jobs/${jobId}`),

  // Calibration & Ground Audits
  uploadGroundPlots: (formData: FormData) =>
    apiRequest<{ project_id: string; imported_plots: number }>('/calibration/plots', {
      method: 'POST',
      body: formData,
    }),

  fitCalibration: (payload: CalibrationFitRequest) =>
    apiRequest<CalibrationStatusResponse>('/calibration/fit', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getCalibrationStatus: (projectId: string) =>
    apiRequest<CalibrationStatusResponse>(`/calibration/status/${projectId}`),

  // Survey Results & Spatial Queries
  getResults: (surveyId: string) =>
    apiRequest<SurveyResultsSummary>(`/results/${surveyId}`),

  getLatestResults: () =>
    apiRequest<SurveyResultsSummary>('/results/latest/summary'),

  getVectors: () =>
    apiRequest<any>('/results/latest/geojson'),

  queryRegion: (surveyId: string, polygonGeoJSON: unknown) =>
    apiRequest<SurveyResultsSummary>(`/results/${surveyId}/region`, {
      method: 'POST',
      body: JSON.stringify({ polygon: polygonGeoJSON }),
    }),

  // Temporal Change Detection
  compareSurveys: (survey1Id: string, survey2Id: string) =>
    apiRequest<SurveyComparisonResponse>(`/compare/${survey1Id}/${survey2Id}`),

  // Active Learning & Field Verification
  getVerificationQueue: (surveyId: string, limit = 50) =>
    apiRequest<TreeQueueItem[]>(`/verify/queue/${surveyId}?limit=${limit}`),

  submitVerification: (payload: VerificationCreate) =>
    apiRequest<VerificationResponse>('/verify', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // Export URLs
  getExportUrl: (surveyId: string, format: 'geojson' | 'csv' | 'pdf') =>
    `${API_BASE}/export/${surveyId}?format=${format}`,
};
