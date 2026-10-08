import React, { useState, useEffect } from 'react';
import { useProject } from '../context/ProjectContext';
import { api } from '../api/client';
import type { SurveyResultsSummary, GeoJSONFeature } from '../types/api';
import { Badge } from '../components/common/Badge';
import {
  Download,
  FileCode,
  FileSpreadsheet,
  FileText,
  Search,
  ExternalLink,
  Layers,
} from 'lucide-react';

export const ExportPage: React.FC = () => {
  const { activeSurvey } = useProject();

  const [results, setResults] = useState<SurveyResultsSummary | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (!activeSurvey) return;
    api.getResults(activeSurvey.id)
      .then((res) => setResults(res.data))
      .catch(() => {});
  }, [activeSurvey]);

  if (!activeSurvey) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
        <Layers size={40} style={{ marginBottom: '1rem', opacity: 0.5 }} />
        <h2>No Survey Selected</h2>
        <p style={{ fontSize: '0.85rem' }}>Select an aerial survey to export data and generate certification dossiers.</p>
      </div>
    );
  }

  const features = results?.geojson?.features || [];
  const filteredFeatures = features.filter((f: GeoJSONFeature) =>
    f.properties.tree_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.properties.status.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ padding: '1.75rem', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Page Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
          MRV Reporting & Data Interoperability
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Export GIS-ready vectors, tree-level inventory spreadsheets, and regulatory carbon dossiers compliant with Verra VM0047, Gold Standard, and Plan Vivo MRV protocols.
        </p>
      </div>

      {/* Export Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {/* Card 1: GeoJSON */}
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: 42, height: 42, borderRadius: 'var(--radius-md)', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileCode size={22} color="#38bdf8" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>
                GeoJSON Crown Vectors
              </h2>
              <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                RFC 7946 Standard (.geojson)
              </span>
            </div>
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', flex: 1 }}>
            Polygons for every segmented tree canopy crown, complete with computed biomass, carbon stock, DBH estimates, and field audit status attributes for GIS tools (QGIS, ArcGIS).
          </p>

          <a
            href={api.getExportUrl(activeSurvey.id, 'geojson')}
            download={`${activeSurvey.original_filename}_crowns.geojson`}
            className="btn btn-primary"
            style={{ width: '100%', gap: '0.5rem' }}
          >
            <Download size={15} />
            <span>Download GeoJSON</span>
          </a>
        </div>

        {/* Card 2: Stand Inventory CSV */}
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: 42, height: 42, borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileSpreadsheet size={22} color="var(--emerald-400)" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>
                Stand Inventory CSV
              </h2>
              <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                Tabular Inventory (.csv)
              </span>
            </div>
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', flex: 1 }}>
            Complete per-tree inventory table containing centroid coordinates, projected crown area (m²), allometric DBH (cm), individual carbon stock (kg), and 90% confidence intervals.
          </p>

          <a
            href={api.getExportUrl(activeSurvey.id, 'csv')}
            download={`${activeSurvey.original_filename}_inventory.csv`}
            className="btn btn-secondary"
            style={{ width: '100%', gap: '0.5rem' }}
          >
            <Download size={15} />
            <span>Download Stand CSV</span>
          </a>
        </div>

        {/* Card 3: MRV Certification Dossier */}
        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: 42, height: 42, borderRadius: 'var(--radius-md)', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileText size={22} color="#f59e0b" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>
                MRV Carbon Audit Report
              </h2>
              <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                Certification Dossier (.pdf)
              </span>
            </div>
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', flex: 1 }}>
            Formal verification document certifying total stand carbon tonnage, conformal prediction bounds, IPCC Tier-3 model metadata, and forester audit trails for carbon registry submission.
          </p>

          <a
            href={api.getExportUrl(activeSurvey.id, 'pdf')}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
            style={{ width: '100%', gap: '0.5rem' }}
          >
            <ExternalLink size={15} />
            <span>Generate PDF Audit Dossier</span>
          </a>
        </div>
      </div>

      {/* Stand Inventory Table Preview */}
      <div className="glass-card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff' }}>
              Tree Inventory Live Preview ({features.length} records)
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
              Previewing calculated crown attributes for active survey
            </p>
          </div>

          {/* Search Input */}
          <div style={{ position: 'relative', width: 260 }}>
            <Search size={15} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Filter by Tree ID or status..."
              className="input-field"
              style={{ paddingLeft: '2.2rem', fontSize: '0.75rem', height: 34 }}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.775rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '0.65rem 0.85rem' }}>TREE ID</th>
                <th style={{ padding: '0.65rem 0.85rem' }}>CROWN AREA</th>
                <th style={{ padding: '0.65rem 0.85rem' }}>EST. DBH</th>
                <th style={{ padding: '0.65rem 0.85rem' }}>BIOMASS (AGB)</th>
                <th style={{ padding: '0.65rem 0.85rem' }}>CARBON STOCK</th>
                <th style={{ padding: '0.65rem 0.85rem' }}>CONFIDENCE</th>
                <th style={{ padding: '0.65rem 0.85rem' }}>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {filteredFeatures.slice(0, 25).map((f: GeoJSONFeature) => (
                <tr key={f.properties.tree_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                  <td style={{ padding: '0.65rem 0.85rem', fontWeight: 600, color: '#ffffff' }}>
                    <code className="font-mono">{f.properties.tree_id}</code>
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem' }} className="font-mono">
                    {f.properties.crown_area_sqm.toFixed(1)} m²
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem' }} className="font-mono">
                    {f.properties.dbh_cm.toFixed(1)} cm
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem' }} className="font-mono">
                    {f.properties.biomass_kg.toFixed(1)} kg
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem' }} className="font-mono">
                    <strong style={{ color: 'var(--emerald-400)' }}>
                      {f.properties.carbon_kg.toFixed(2)} kg
                    </strong>
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem' }} className="font-mono">
                    {(f.properties.confidence * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '0.65rem 0.85rem' }}>
                    <Badge
                      variant={
                        f.properties.status === 'verified'
                          ? 'calibrated'
                          : f.properties.status === 'rejected'
                          ? 'danger'
                          : 'default'
                      }
                      label={f.properties.status}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredFeatures.length > 25 && (
          <div style={{ textAlign: 'center', padding: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Showing 25 of {filteredFeatures.length} records. Download full CSV or GeoJSON above for complete stand dataset.
          </div>
        )}
      </div>
    </div>
  );
};
