import React, { useState } from 'react';
import { useProject } from '../context/ProjectContext';
import { api } from '../api/client';
import type { SurveyComparisonResponse } from '../types/api';
import { Badge } from '../components/common/Badge';
import {
  GitCompare,
  TrendingUp,
  TrendingDown,
  TreePine,
  MinusCircle,
  PlusCircle,
  ArrowUpRight,
  Loader2,
} from 'lucide-react';

export const ComparePage: React.FC = () => {
  const { surveys } = useProject();

  const [survey1Id, setSurvey1Id] = useState<string>(surveys[0]?.id || '');
  const [survey2Id, setSurvey2Id] = useState<string>(surveys[1]?.id || surveys[0]?.id || '');

  const [comparison, setComparison] = useState<SurveyComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunComparison = async () => {
    if (!survey1Id || !survey2Id) {
      setError('Please select both a baseline and comparison survey.');
      return;
    }
    if (survey1Id === survey2Id) {
      setError('Baseline and comparison surveys must be distinct flights to detect temporal changes.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.compareSurveys(survey1Id, survey2Id);
      setComparison(res.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '1.75rem', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Page Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
          Temporal Stand Evolution & Change Detection
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Compare multi-temporal UAV orthomosaics across flight dates (T1 Baseline vs T2 Re-survey) to track tree recruitment, mortality, canopy expansion, and net stand carbon sequestration.
        </p>
      </div>

      {/* Flight Selection Bar */}
      <div className="glass-card" style={{ padding: '1.25rem 1.5rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1, minWidth: 220 }}>
          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Baseline Survey (Time T1)
          </label>
          <select
            aria-label="Baseline Survey (Time T1)"
            className="input-field"
            value={survey1Id}
            onChange={(e) => setSurvey1Id(e.target.value)}
          >
            <option value="">Select baseline flight...</option>
            {surveys.map((s) => (
              <option key={s.id} value={s.id}>
                {s.original_filename} ({s.capture_date || 'Undated'})
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', paddingTop: '1.2rem' }}>
          <GitCompare size={20} color="var(--emerald-400)" />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1, minWidth: 220 }}>
          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            Comparison Survey (Time T2)
          </label>
          <select
            aria-label="Comparison Survey (Time T2)"
            className="input-field"
            value={survey2Id}
            onChange={(e) => setSurvey2Id(e.target.value)}
          >
            <option value="">Select comparison flight...</option>
            {surveys.map((s) => (
              <option key={s.id} value={s.id}>
                {s.original_filename} ({s.capture_date || 'Undated'})
              </option>
            ))}
          </select>
        </div>

        <div style={{ paddingTop: '1.2rem' }}>
          <button
            onClick={handleRunComparison}
            disabled={loading || !survey1Id || !survey2Id}
            className="btn btn-primary"
            style={{ gap: '0.5rem', height: 38 }}
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <GitCompare size={16} />}
            <span>{loading ? 'Analyzing...' : 'Run Stand Comparison'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: '0.75rem 1rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            fontSize: '0.825rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Comparison Results Dashboard */}
      {comparison && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Net Stand Delta Hero */}
          <div
            className="glass-card"
            style={{
              padding: '1.5rem',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(9, 15, 12, 0.95) 100%)',
              border: '1px solid var(--border-focus)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1.5rem',
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--emerald-400)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Net Temporal Stand Dynamics
                </span>
                <Badge
                  variant={comparison.data_source === 'synthetic' ? 'synthetic' : 'real'}
                  label={comparison.data_source === 'synthetic' ? 'Synthetic Demo' : 'Real Inferences'}
                />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', margin: 0 }}>
                {comparison.net_carbon_change_kg >= 0 ? '+' : ''}
                {(comparison.net_carbon_change_kg / 1000).toFixed(2)} t CO₂e Net Sequestration
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                Net stem population delta: {comparison.net_tree_change >= 0 ? `+${comparison.net_tree_change}` : comparison.net_tree_change} trees
              </p>
            </div>

            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Net Carbon Change</div>
                <div
                  className="font-mono"
                  style={{
                    fontSize: '1.25rem',
                    fontWeight: 800,
                    color: comparison.net_carbon_change_kg >= 0 ? 'var(--emerald-400)' : '#f87171',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                    justifyContent: 'flex-end',
                  }}
                >
                  {comparison.net_carbon_change_kg >= 0 ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
                  <span>{comparison.net_carbon_change_kg.toFixed(1)} kg</span>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Net Canopy Population</div>
                <div
                  className="font-mono"
                  style={{
                    fontSize: '1.25rem',
                    fontWeight: 800,
                    color: comparison.net_tree_change >= 0 ? 'var(--emerald-400)' : '#f87171',
                  }}
                >
                  {comparison.net_tree_change >= 0 ? `+${comparison.net_tree_change}` : comparison.net_tree_change}
                </div>
              </div>
            </div>
          </div>

          {/* 4 Category Change Breakdown Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            {/* 1. New Trees */}
            <div
              className="glass-card"
              style={{
                padding: '1.25rem',
                borderLeft: '4px solid #10b981',
                background: 'rgba(16, 185, 129, 0.04)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <PlusCircle size={18} color="#10b981" />
                  <span style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.9rem' }}>New Ingrowth</span>
                </div>
                <span className="font-mono" style={{ fontSize: '1.1rem', fontWeight: 800, color: '#10b981' }}>
                  +{comparison.new_trees.count}
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Newly established trees or young saplings detected in re-survey.
              </p>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Carbon: <strong style={{ color: '#ffffff' }}>{comparison.new_trees.total_carbon_kg.toFixed(1)} kg</strong>
                <br />
                Mean Area: <strong style={{ color: '#ffffff' }}>{comparison.new_trees.mean_crown_area_sqm.toFixed(1)} m²</strong>
              </div>
            </div>

            {/* 2. Lost Trees */}
            <div
              className="glass-card"
              style={{
                padding: '1.25rem',
                borderLeft: '4px solid #ef4444',
                background: 'rgba(239, 68, 68, 0.04)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <MinusCircle size={18} color="#ef4444" />
                  <span style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.9rem' }}>Lost / Mortality</span>
                </div>
                <span className="font-mono" style={{ fontSize: '1.1rem', fontWeight: 800, color: '#ef4444' }}>
                  -{comparison.lost_trees.count}
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Trees present in baseline but absent in re-survey (fell, died, harvested).
              </p>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Carbon Lost: <strong style={{ color: '#ffffff' }}>{comparison.lost_trees.total_carbon_kg.toFixed(1)} kg</strong>
                <br />
                Mean Area: <strong style={{ color: '#ffffff' }}>{comparison.lost_trees.mean_crown_area_sqm.toFixed(1)} m²</strong>
              </div>
            </div>

            {/* 3. Grown Trees */}
            <div
              className="glass-card"
              style={{
                padding: '1.25rem',
                borderLeft: '4px solid #f59e0b',
                background: 'rgba(245, 158, 11, 0.04)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <ArrowUpRight size={18} color="#f59e0b" />
                  <span style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.9rem' }}>Canopy Growth</span>
                </div>
                <span className="font-mono" style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f59e0b' }}>
                  {comparison.grown_trees.count}
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Surviving trees showing measurable canopy crown expansion.
              </p>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Stock: <strong style={{ color: '#ffffff' }}>{comparison.grown_trees.total_carbon_kg.toFixed(1)} kg</strong>
                <br />
                Mean Area: <strong style={{ color: '#ffffff' }}>{comparison.grown_trees.mean_crown_area_sqm.toFixed(1)} m²</strong>
              </div>
            </div>

            {/* 4. Unchanged Trees */}
            <div
              className="glass-card"
              style={{
                padding: '1.25rem',
                borderLeft: '4px solid #64748b',
                background: 'rgba(100, 116, 139, 0.04)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <TreePine size={18} color="#94a3b8" />
                  <span style={{ fontWeight: 700, color: '#ffffff', fontSize: '0.9rem' }}>Stable / Unchanged</span>
                </div>
                <span className="font-mono" style={{ fontSize: '1.1rem', fontWeight: 800, color: '#94a3b8' }}>
                  {comparison.unchanged_trees.count}
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Mature trees with constant canopy area within statistical noise.
              </p>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Stock: <strong style={{ color: '#ffffff' }}>{comparison.unchanged_trees.total_carbon_kg.toFixed(1)} kg</strong>
                <br />
                Mean Area: <strong style={{ color: '#ffffff' }}>{comparison.unchanged_trees.mean_crown_area_sqm.toFixed(1)} m²</strong>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
