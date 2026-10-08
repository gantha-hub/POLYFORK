import React, { useState, useRef } from 'react';
import { useProject } from '../context/ProjectContext';
import { api } from '../api/client';
import { Badge } from '../components/common/Badge';
import {
  Scale,
  UploadCloud,
  FileSpreadsheet,
  Activity,
  Sparkles,
} from 'lucide-react';

export const CalibrationPage: React.FC = () => {
  const { activeProject, calibration, refreshCalibration } = useProject();

  // Plot CSV upload state
  const plotFileInputRef = useRef<HTMLInputElement>(null);
  const [selectedCsv, setSelectedCsv] = useState<File | null>(null);
  const [isUploadingPlots, setIsUploadingPlots] = useState(false);
  const [uploadPlotMsg, setUploadPlotMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Model fitting state
  const [method, setMethod] = useState<'negbin_glm' | 'ratio'>('negbin_glm');
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.90);
  const [isFitting, setIsFitting] = useState(false);
  const [fitMsg, setFitMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleUploadPlots = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeProject) {
      setUploadPlotMsg({ type: 'error', text: 'Select a project first.' });
      return;
    }
    if (!selectedCsv) {
      setUploadPlotMsg({ type: 'error', text: 'Please choose a CSV file with ground plots.' });
      return;
    }

    setIsUploadingPlots(true);
    setUploadPlotMsg(null);
    try {
      const formData = new FormData();
      formData.append('file', selectedCsv);
      formData.append('project_id', activeProject.id);

      const res = await api.uploadGroundPlots(formData);
      setUploadPlotMsg({
        type: 'success',
        text: `Successfully imported ${res.data.imported_plots} ground audit plots.`,
      });
      setSelectedCsv(null);
      await refreshCalibration();
    } catch (err: unknown) {
      setUploadPlotMsg({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to upload ground plots',
      });
    } finally {
      setIsUploadingPlots(false);
    }
  };

  const handleFitCalibration = async () => {
    if (!activeProject) {
      setFitMsg({ type: 'error', text: 'No active project selected.' });
      return;
    }

    setIsFitting(true);
    setFitMsg(null);
    try {
      await api.fitCalibration({
        project_id: activeProject.id,
        method,
        confidence_level: confidenceLevel,
      });
      await refreshCalibration();
      setFitMsg({
        type: 'success',
        text: `Successfully fit ${method.toUpperCase()} with conformal ${Math.round(confidenceLevel * 100)}% coverage!`,
      });
    } catch (err: unknown) {
      setFitMsg({
        type: 'error',
        text: err instanceof Error ? err.message : 'Calibration fitting failed',
      });
    } finally {
      setIsFitting(false);
    }
  };

  return (
    <div style={{ padding: '1.75rem', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Page Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
          Allometric Ground Truth Calibration
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Ground audit plot integration and Split Conformal Prediction engine. Calibrates raw remote-sensing crown models against destructive or field-measured DBH plot tallies with distribution-free finite-sample coverage guarantees.
        </p>
      </div>

      {/* Current Calibration Status Hero Card */}
      <div
        className="glass-card"
        style={{
          padding: '1.5rem',
          background: calibration?.calibrated
            ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(9, 15, 12, 0.95) 100%)'
            : 'rgba(9, 15, 12, 0.95)',
          border: calibration?.calibrated
            ? '1px solid var(--border-focus)'
            : '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: 42,
                height: 42,
                borderRadius: 'var(--radius-md)',
                background: calibration?.calibrated ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Scale size={24} color={calibration?.calibrated ? 'var(--emerald-400)' : '#f59e0b'} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#ffffff', margin: 0 }}>
                {calibration?.calibrated ? 'Active Model Calibrated' : 'Stand Model Uncalibrated'}
              </h2>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Project: {activeProject?.name || 'None'}
              </span>
            </div>
          </div>

          <Badge
            variant={calibration?.calibrated ? 'calibrated' : 'uncalibrated'}
            label={calibration?.calibrated ? 'Statistically Certified' : 'Raw Model Only'}
          />
        </div>

        {calibration?.calibrated ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Calibrated Method</div>
              <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>
                {calibration.method === 'negbin_glm' ? 'Negative Binomial GLM' : 'Ratio Estimator'}
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Ground Calibration Plots</div>
              <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--emerald-400)' }}>
                {calibration.n_plots ?? '—'} field plots
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Conformal Coverage Level</div>
              <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>
                {calibration.empirical_coverage ? `${(calibration.empirical_coverage * 100).toFixed(1)}%` : '90.0%'}
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Nonconformity Quantile (q)</div>
              <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#38bdf8' }}>
                {calibration.residual_quantile_q ? calibration.residual_quantile_q.toFixed(3) : '—'}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            No ground plots are calibrated for this project yet. Ingest field plot tallies below to enable finite-sample uncertainty quantification brackets.
          </div>
        )}
      </div>

      {/* Calibration Parameters Table if calibrated */}
      {calibration?.calibrated && calibration.params && (
        <div className="glass-card" style={{ padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={18} color="var(--emerald-400)" />
            <span>Fitted Statistical Coefficients</span>
          </h2>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.6rem 1rem' }}>PARAMETER / FEATURE</th>
                  <th style={{ padding: '0.6rem 1rem' }}>ESTIMATED COEFFICIENT</th>
                  <th style={{ padding: '0.6rem 1rem' }}>INTERPRETATION</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(calibration.params.coefficients || {}).map(([feature, coef]) => (
                  <tr key={feature} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#ffffff' }}>
                      <code className="font-mono">{feature}</code>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }} className="font-mono">
                      <span style={{ color: 'var(--emerald-400)', fontWeight: 700 }}>
                        {typeof coef === 'number' ? coef.toFixed(4) : coef}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)' }}>
                      {feature === 'intercept'
                        ? 'Base baseline stem log-intensity'
                        : `Log-linear scaling with ${feature}`}
                    </td>
                  </tr>
                ))}
                {calibration.params.dispersion_alpha !== undefined && (
                  <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#ffffff' }}>
                      <code className="font-mono">dispersion_alpha</code>
                    </td>
                    <td style={{ padding: '0.75rem 1rem' }} className="font-mono">
                      <span style={{ color: '#fbbf24', fontWeight: 700 }}>
                        {calibration.params.dispersion_alpha.toFixed(4)}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)' }}>
                      Negative Binomial overdispersion parameter (variance = $\mu + \alpha \mu^2$)
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Two Column Actions: Upload Plots & Fit Calibration */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
        {/* Step 1: Upload Field Plots */}
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileSpreadsheet size={18} color="var(--emerald-400)" />
            <span>Step 1: Ingest Ground Plots (CSV)</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
            Upload destructive harvesting plots or sample inventory tallies (fields: <code>plot_id</code>, <code>crown_area_sqm</code>, <code>stem_count</code>, <code>biomass_kg</code>).
          </p>

          <form onSubmit={handleUploadPlots} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: 'auto' }}>
            <div
              onClick={() => plotFileInputRef.current?.click()}
              style={{
                border: '2px dashed',
                borderColor: selectedCsv ? 'var(--emerald-400)' : 'var(--border-card)',
                borderRadius: 'var(--radius-md)',
                padding: '1.25rem',
                textAlign: 'center',
                background: selectedCsv ? 'rgba(16, 185, 129, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                cursor: 'pointer',
              }}
            >
              <input
                ref={plotFileInputRef}
                type="file"
                accept=".csv"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setSelectedCsv(e.target.files[0]);
                    setUploadPlotMsg(null);
                  }
                }}
                style={{ display: 'none' }}
              />
              <UploadCloud size={28} color={selectedCsv ? 'var(--emerald-400)' : 'var(--text-muted)'} style={{ margin: '0 auto 0.4rem' }} />
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#ffffff' }}>
                {selectedCsv ? selectedCsv.name : 'Choose ground_plots.csv'}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                Field inventory spreadsheet
              </div>
            </div>

            {uploadPlotMsg && (
              <div
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.775rem',
                  background: uploadPlotMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: uploadPlotMsg.type === 'success' ? 'var(--emerald-400)' : '#f87171',
                }}
              >
                {uploadPlotMsg.text}
              </div>
            )}

            <button
              type="submit"
              disabled={isUploadingPlots || !selectedCsv}
              className="btn btn-secondary"
              style={{ width: '100%' }}
            >
              {isUploadingPlots ? 'Uploading Plots...' : 'Upload Ground Plots'}
            </button>
          </form>
        </div>

        {/* Step 2: Fit Calibration Model */}
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} color="var(--emerald-400)" />
            <span>Step 2: Fit Allometric Estimator</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
            Execute rigorous split conformalization over plot residuals to calculate confidence multiplier $q$.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: 'auto' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                Statistical Estimator
              </label>
              <select
                aria-label="Statistical Estimator"
                className="input-field"
                value={method}
                onChange={(e) => setMethod(e.target.value as 'negbin_glm' | 'ratio')}
              >
                <option value="negbin_glm">Negative Binomial GLM (Handles Overdispersion)</option>
                <option value="ratio">Ratio Estimator (Mean of Ratios)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                Conformal Coverage Guarantee (1 - α)
              </label>
              <select
                aria-label="Conformal Coverage Guarantee"
                className="input-field font-mono"
                value={confidenceLevel}
                onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
              >
                <option value={0.95}>95% Conformal Confidence (α = 0.05)</option>
                <option value={0.90}>90% Conformal Confidence (α = 0.10 - Recommended)</option>
                <option value={0.80}>80% Conformal Confidence (α = 0.20)</option>
              </select>
            </div>

            {fitMsg && (
              <div
                style={{
                  padding: '0.5rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.775rem',
                  background: fitMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: fitMsg.type === 'success' ? 'var(--emerald-400)' : '#f87171',
                }}
              >
                {fitMsg.text}
              </div>
            )}

            <button
              onClick={handleFitCalibration}
              disabled={isFitting || !activeProject}
              className="btn btn-primary"
              style={{ width: '100%' }}
            >
              {isFitting ? 'Fitting Allometry & Bounds...' : 'Fit Conformal Calibration'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
