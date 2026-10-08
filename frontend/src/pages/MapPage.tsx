import React, { useEffect, useState } from 'react';
import { useProject } from '../context/ProjectContext';
import { api } from '../api/client';
import type { SurveyResultsSummary, GeoJSONFeatureProperties } from '../types/api';
import { StandMap } from '../components/map/StandMap';
import { TreeDrawer } from '../components/map/TreeDrawer';
import { StatCard } from '../components/common/StatCard';
import { Badge } from '../components/common/Badge';
import {
  Trees,
  Flame,
  Ruler,
  Layers,
  AlertCircle,
  Loader2,
  UploadCloud,
} from 'lucide-react';

interface MapPageProps {
  onNavigateToSurveys: () => void;
}

export const MapPage: React.FC<MapPageProps> = ({ onNavigateToSurveys }) => {
  const { activeSurvey, calibration } = useProject();
  const [results, setResults] = useState<SurveyResultsSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTree, setSelectedTree] = useState<GeoJSONFeatureProperties | null>(null);

  useEffect(() => {
    if (!activeSurvey) {
      setResults(null);
      setSelectedTree(null);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);
    setSelectedTree(null);

    api.getResults(activeSurvey.id)
      .then((res) => {
        if (isMounted) {
          setResults(res.data);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load survey results');
        }
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [activeSurvey]);

  const handleUpdateTreeStatus = (treeId: string, newStatus: GeoJSONFeatureProperties['status']) => {
    if (!results || !results.geojson) return;

    // Mutate local state so map and drawer reflect verification instantly
    const updatedFeatures = results.geojson.features.map((feat) => {
      if (feat.properties.tree_id === treeId) {
        return {
          ...feat,
          properties: {
            ...feat.properties,
            status: newStatus,
          },
        };
      }
      return feat;
    });

    setResults({
      ...results,
      geojson: {
        ...results.geojson,
        features: updatedFeatures,
      },
    });

    if (selectedTree && selectedTree.tree_id === treeId) {
      setSelectedTree({
        ...selectedTree,
        status: newStatus,
      });
    }
  };

  if (!activeSurvey) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          padding: '2rem',
          textAlign: 'center',
        }}
      >
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'rgba(16, 185, 129, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '1rem',
          }}
        >
          <Layers size={32} color="var(--emerald-400)" />
        </div>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: '#ffffff' }}>
          No Survey Selected
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: 420, marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          To view the Digital Twin, select an existing survey from the top bar or ingest a new aerial drone orthomosaic.
        </p>
        <button onClick={onNavigateToSurveys} className="btn btn-primary" style={{ gap: '0.5rem' }}>
          <UploadCloud size={16} />
          <span>Go to Surveys & Ingestion</span>
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', position: 'relative' }}>
      {/* Top Stand Summary KPIs */}
      <div
        style={{
          background: 'rgba(9, 15, 12, 0.95)',
          borderBottom: '1px solid var(--border-subtle)',
          padding: '0.75rem 1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h1 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#ffffff', margin: 0 }}>
              {activeSurvey.original_filename}
            </h1>
            <Badge variant="default" label={activeSurvey.forest_type.toUpperCase()} />
            {results && (
              <Badge
                variant={results.data_source === 'synthetic' ? 'synthetic' : 'real'}
                label={results.data_source === 'synthetic' ? 'Synthetic Demo Stand' : 'Real Model Inferences'}
              />
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Badge
              variant={calibration?.calibrated ? 'calibrated' : 'uncalibrated'}
              label={calibration?.calibrated ? 'Calibrated Allometry' : 'Raw Uncalibrated'}
            />
          </div>
        </div>

        {/* Metric Cards Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
          <StatCard
            title="Total Stand Trees"
            value={results ? results.count.calibrated_count : '—'}
            unit="trees"
            interval={
              results && results.count.interval
                ? {
                    low: results.count.interval.low,
                    high: results.count.interval.high,
                    confidenceLevel: results.count.interval.confidence_level,
                  }
                : undefined
            }
            icon={<Trees size={18} />}
          />

          <StatCard
            title="Total Carbon Stock"
            value={results ? results.carbon.mean_carbon_tonnes.toFixed(2) : '—'}
            unit="t CO₂e"
            interval={
              results && results.carbon.interval_tonnes
                ? {
                    low: results.carbon.interval_tonnes.low,
                    high: results.carbon.interval_tonnes.high,
                    confidenceLevel: results.carbon.interval_tonnes.confidence_level,
                  }
                : undefined
            }
            icon={<Flame size={18} />}
            accentColor="var(--emerald-400)"
          />

          <StatCard
            title="Mean Crown Area"
            value={results ? results.mean_crown_area_sqm.toFixed(1) : '—'}
            unit="m²"
            icon={<Ruler size={18} />}
          />

          <StatCard
            title="Mean Stand DBH"
            value={results ? results.mean_dbh_cm.toFixed(1) : '—'}
            unit="cm"
            icon={<Trees size={18} />}
          />
        </div>
      </div>

      {/* Main Map Viewport & Drawer */}
      <div style={{ flex: 1, position: 'relative', width: '100%', height: '100%', minHeight: 0 }}>
        {loading ? (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(6, 10, 8, 0.85)',
              zIndex: 800,
              gap: '0.75rem',
            }}
          >
            <Loader2 size={36} color="var(--emerald-400)" className="animate-spin" />
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Loading stand canopy geometry & allometrics...
            </div>
          </div>
        ) : error ? (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 800,
              gap: '0.75rem',
              padding: '2rem',
              textAlign: 'center',
            }}
          >
            <AlertCircle size={40} color="#ef4444" />
            <h3 style={{ color: '#ffffff' }}>Failed to Load Stand Results</h3>
            <p style={{ color: '#f87171', fontSize: '0.85rem', maxWidth: 450 }}>{error}</p>
          </div>
        ) : (
          <StandMap
            geojson={results?.geojson || null}
            selectedTreeId={selectedTree?.tree_id || null}
            onSelectTree={(tree) => setSelectedTree(tree)}
          />
        )}

        {/* Tree Details Drawer */}
        <TreeDrawer
          tree={selectedTree}
          onClose={() => setSelectedTree(null)}
          onUpdateTreeStatus={handleUpdateTreeStatus}
        />
      </div>
    </div>
  );
};
