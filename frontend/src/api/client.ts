/**
 * Type-safe API client for VrikshaVision backend.
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

const API_BASE = import.meta.env.VITE_API_URL || '/api';

/**
 * Standard fetch wrapper that unwraps ResponseEnvelope.
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

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } else if (errJson.error?.message) {
        errorMsg = errJson.error.message;
      }
    } catch {
      // Use fallback errorMsg
    }
    throw new Error(errorMsg);
  }

  return response.json();
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
