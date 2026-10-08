import React, { useState, useRef } from 'react';
import { useProject } from '../context/ProjectContext';
import { api } from '../api/client';
import type { JobResponse, SurveyResponse } from '../types/api';
import { ProgressBar } from '../components/common/ProgressBar';
import { Badge } from '../components/common/Badge';
import {
  UploadCloud,
  FileCheck,
  Clock,
  Layers,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  FolderOpen,
} from 'lucide-react';

interface SurveysPageProps {
  onNavigateToMap: () => void;
}

export const SurveysPage: React.FC<SurveysPageProps> = ({ onNavigateToMap }) => {
  const { activeProject, surveys, activeSurvey, setActiveSurvey, refreshSurveys } = useProject();

  // Upload Form State
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [forestType, setForestType] = useState('tropical_broadleaf');
  const [resolutionM, setResolutionM] = useState('0.05');
  const [captureDate, setCaptureDate] = useState(new Date().toISOString().split('T')[0]);

  // Ingestion Processing Job State
  const [isUploading, setIsUploading] = useState(false);
  const [activeJob, setActiveJob] = useState<JobResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleStartIngestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) {
      setUploadError('Please select or create a project first.');
      return;
    }
    if (!selectedFile) {
      setUploadError('Please select a raster or GeoTIFF file to upload.');
      return;
    }

    setIsUploading(true);
    setUploadError(null);
    setActiveJob(null);

    try {
      // 1. Upload Raster
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('project_id', activeProject.id);
      formData.append('forest_type', forestType);
      formData.append('resolution_m', resolutionM);
      formData.append('capture_date', captureDate);

      const uploadRes = await api.uploadRaster(formData);
      const newSurvey = uploadRes.data;

      // 2. Start Processing Job
      const jobRes = await api.startJob(newSurvey.id);
      setActiveJob(jobRes.data);

      // 3. Poll Job Status
      const pollInterval = window.setInterval(async () => {
        try {
          const statusRes = await api.getJobStatus(jobRes.data.id);
          setActiveJob(statusRes.data);

          if (statusRes.data.status === 'completed') {
            clearInterval(pollInterval);
            setIsUploading(false);
            await refreshSurveys();
            setActiveSurvey(newSurvey);
          } else if (statusRes.data.status === 'failed') {
            clearInterval(pollInterval);
            setIsUploading(false);
            setUploadError(statusRes.data.error || 'Canopy processing pipeline failed.');
          }
        } catch (pollErr: unknown) {
          clearInterval(pollInterval);
          setIsUploading(false);
          setUploadError(pollErr instanceof Error ? pollErr.message : 'Error checking job status');
        }
      }, 1500);
    } catch (err: unknown) {
      setIsUploading(false);
      setUploadError(err instanceof Error ? err.message : 'Failed to upload orthomosaic');
    }
  };

  return (
    <div style={{ padding: '1.75rem', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Page Title */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
          Aerial Survey Ingestion & Registry
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Upload high-resolution UAV orthomosaics (GeoTIFF) to trigger automated deep-learning canopy segmentation, allometric DBH scaling, and conformal biomass quantification.
        </p>
      </div>

      {/* Grid: Upload Box on Left, Ingestion Pipeline on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 460px) 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Upload Form Card */}
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <UploadCloud size={20} color="var(--emerald-400)" />
            <span>Upload New Survey</span>
          </h2>

          <form onSubmit={handleStartIngestion} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* File Dropzone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: '2px dashed',
                borderColor: selectedFile ? 'var(--emerald-400)' : 'var(--border-card)',
                borderRadius: 'var(--radius-lg)',
                padding: '1.5rem 1rem',
                textAlign: 'center',
                background: selectedFile ? 'rgba(16, 185, 129, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".tif,.tiff,.geojson,.zip,.png,.jpg,.jpeg"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />

              {selectedFile ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem' }}>
                  <FileCheck size={32} color="var(--emerald-400)" />
                  <span style={{ fontWeight: 600, color: '#ffffff', fontSize: '0.875rem' }}>
                    {selectedFile.name}
                  </span>
                  <span className="font-mono" style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </span>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.4rem' }}>
                  <FolderOpen size={32} color="var(--text-muted)" />
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                    Click to browse or drop raster
                  </span>
                  <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                    GeoTIFF (.tif), Orthomosaic, or Stand GeoJSON
                  </span>
                </div>
              )}
            </div>

            {/* Forest Type */}
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                Forest Allometric Biome
              </label>
              <select
                aria-label="Forest Allometric Biome"
                className="input-field"
                value={forestType}
                onChange={(e) => setForestType(e.target.value)}
              >
                <option value="tropical_broadleaf">Tropical Moist Broadleaf (Chave 2014 Pan-tropical)</option>
                <option value="temperate_conifer">Temperate Conifer (Jenkins et al.)</option>
                <option value="boreal">Boreal Forest (Scots Pine / Birch)</option>
                <option value="agroforest">Agroforestry / Plantation (Teak / Eucalyptus)</option>
              </select>
            </div>

            {/* Resolution and Date Row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Spatial GSD (m/px)
                </label>
                <input
                  type="number"
                  step="0.01"
                  className="input-field font-mono"
                  value={resolutionM}
                  onChange={(e) => setResolutionM(e.target.value)}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  Flight Date
                </label>
                <input
                  type="date"
                  className="input-field"
                  value={captureDate}
                  onChange={(e) => setCaptureDate(e.target.value)}
                />
              </div>
            </div>

            {uploadError && (
              <div
                style={{
                  padding: '0.6rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#f87171',
                  fontSize: '0.775rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
              >
                <AlertTriangle size={15} />
                <span>{uploadError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isUploading || !selectedFile || !activeProject}
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '0.5rem' }}
            >
              {isUploading ? 'Executing Ingestion Pipeline...' : 'Upload & Process Stand'}
            </button>
          </form>
        </div>

        {/* Live Processing Monitor or Status Details */}
        <div className="glass-card" style={{ padding: '1.5rem', minHeight: 380 }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={20} color="var(--emerald-400)" />
            <span>Pipeline Execution Monitor</span>
          </h2>

          {activeJob ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1rem',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Job ID: <code className="font-mono">{activeJob.id}</code>
                  </span>
                  <Badge
                    variant={
                      activeJob.status === 'completed'
                        ? 'calibrated'
                        : activeJob.status === 'failed'
                        ? 'danger'
                        : 'uncalibrated'
                    }
                    label={activeJob.status.toUpperCase()}
                  />
                </div>

                <ProgressBar
                  progress={Math.round(activeJob.progress * 100)}
                  status={
                    activeJob.status === 'completed'
                      ? 'completed'
                      : activeJob.status === 'failed'
                      ? 'failed'
                      : 'processing'
                  }
                  error={activeJob.error}
                />
              </div>

              {activeJob.status === 'completed' && (
                <div
                  style={{
                    padding: '1rem',
                    borderRadius: 'var(--radius-md)',
                    background: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <CheckCircle2 size={24} color="var(--emerald-400)" />
                    <div>
                      <div style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.9rem' }}>
                        Processing Finished
                      </div>
                      <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                        Canopy crowns segmented with full conformal biomass brackets.
                      </div>
                    </div>
                  </div>

                  <button onClick={onNavigateToMap} className="btn btn-primary btn-sm" style={{ gap: '0.4rem' }}>
                    <span>View in Map</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: 240,
                textAlign: 'center',
                color: 'var(--text-muted)',
              }}
            >
              <Layers size={36} style={{ marginBottom: '0.75rem', opacity: 0.4 }} />
              <p style={{ fontSize: '0.85rem', maxWidth: 300 }}>
                No active ingestion job running. Upload an orthomosaic on the left to monitor the AI segmentation stages.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Registered Surveys Table */}
      <div className="glass-card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
              Project Survey History ({surveys.length})
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
              Registered time-series flights in project "{activeProject?.name || 'Selected Project'}"
            </p>
          </div>
        </div>

        {surveys.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No surveys registered in this project yet. Upload your first flight above.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>SURVEY FILE</th>
                  <th style={{ padding: '0.75rem 1rem' }}>FOREST BIOME</th>
                  <th style={{ padding: '0.75rem 1rem' }}>RESOLUTION</th>
                  <th style={{ padding: '0.75rem 1rem' }}>FLIGHT DATE</th>
                  <th style={{ padding: '0.75rem 1rem' }}>ACTIONS</th>
                </tr>
              </thead>
              <tbody>
                {surveys.map((survey: SurveyResponse) => {
                  const isActive = activeSurvey?.id === survey.id;
                  return (
                    <tr
                      key={survey.id}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        background: isActive ? 'rgba(16, 185, 129, 0.05)' : 'transparent',
                      }}
                    >
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <div style={{ fontWeight: 600, color: '#ffffff' }}>{survey.original_filename}</div>
                        <div className="font-mono" style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>
                          ID: {survey.id}
                        </div>
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <Badge variant="default" label={survey.forest_type} />
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }} className="font-mono">
                        {survey.resolution_m ? `${survey.resolution_m} m/px` : '—'}
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        {survey.capture_date || 'N/A'}
                      </td>
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <button
                          onClick={() => {
                            setActiveSurvey(survey);
                            onNavigateToMap();
                          }}
                          className={`btn btn-sm ${isActive ? 'btn-primary' : 'btn-secondary'}`}
                          style={{ gap: '0.35rem' }}
                        >
                          <span>{isActive ? 'Current Active' : 'Inspect Map'}</span>
                          <ArrowRight size={13} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
