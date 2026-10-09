import React, { useState } from 'react';
import type { GeoJSONFeatureProperties } from '../../types/api';
import { Badge } from '../common/Badge';
import { api } from '../../api/client';
import {
  X,
  CheckCircle,
  XCircle,
  TreePine,
  Ruler,
  Weight,
  Flame,
} from 'lucide-react';

interface TreeDrawerProps {
  tree: GeoJSONFeatureProperties | null;
  onClose: () => void;
  onUpdateTreeStatus?: (treeId: string, status: GeoJSONFeatureProperties['status']) => void;
}

export const TreeDrawer: React.FC<TreeDrawerProps> = ({
  tree,
  onClose,
  onUpdateTreeStatus,
}) => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  if (!tree) return null;

  const handleAction = async (action: 'accept' | 'reject') => {
    setIsVerifying(true);
    setFeedbackMsg(null);
    try {
      await api.submitVerification({
        tree_id: tree.tree_id,
        action,
        user_id: 'inspector_local',
        notes: `Quick verified from map inspector as ${action}`,
      });
      const newStatus = action === 'accept' ? 'verified' : 'rejected';
      onUpdateTreeStatus?.(tree.tree_id, newStatus);
      setFeedbackMsg(`Successfully marked as ${newStatus}`);
    } catch (err: unknown) {
      setFeedbackMsg(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <aside className="tree-drawer">
      {/* Mobile Bottom Sheet Pull Handle */}
      <div className="sheet-drag-handle" />

      {/* Header with Title and Close Button */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 'var(--radius-md)',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <TreePine size={22} color="var(--emerald-400)" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>
              Tree #{tree.tree_id.slice(-6)}
            </h3>
            <span className="font-mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {tree.tree_id}
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          aria-label="Close inspector"
          className="btn btn-secondary touch-target"
          style={{ width: 44, height: 44, padding: 0, borderRadius: '50%' }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Badges Section */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        <Badge
          variant={
            tree.status === 'verified'
              ? 'calibrated'
              : tree.status === 'rejected'
              ? 'danger'
              : 'default'
          }
          label={`Status: ${tree.status}`}
        />
        <Badge
          variant={tree.data_source === 'synthetic' ? 'synthetic' : 'real'}
          label={tree.data_source === 'synthetic' ? 'Synthetic Demo' : 'Real Model'}
        />
        <span
          className="font-mono"
          style={{
            fontSize: '0.725rem',
            padding: '0.2rem 0.5rem',
            borderRadius: 'var(--radius-pill)',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
          }}
        >
          Conf: {(tree.confidence * 100).toFixed(1)}%
        </span>
      </div>

      {/* Physical Attributes Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <div
          style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <Ruler size={18} color="var(--emerald-400)" />
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Crown Projected Area</div>
            <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>
              {tree.crown_area_sqm.toFixed(2)} m²
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <TreePine size={18} color="#38bdf8" />
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Estimated DBH (Diameter)</div>
            <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>
              {tree.dbh_cm.toFixed(1)} cm
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <Weight size={18} color="#f59e0b" />
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Aboveground Biomass (AGB)</div>
            <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>
              {tree.biomass_kg.toFixed(1)} kg
            </div>
          </div>
        </div>

        <div
          style={{
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}
        >
          <Flame size={18} color="var(--emerald-400)" />
          <div>
            <div style={{ fontSize: '0.7rem', color: 'var(--emerald-400)' }}>Stored Carbon Stock</div>
            <div className="font-mono" style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--emerald-400)' }}>
              {tree.carbon_kg.toFixed(2)} kg CO₂e
            </div>
          </div>
        </div>
      </div>

      {/* Field Auditor Verification Section */}
      <div
        style={{
          marginTop: 'auto',
          paddingTop: '1rem',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Field Auditor Actions
        </div>

        {feedbackMsg && (
          <div
            style={{
              fontSize: '0.75rem',
              padding: '0.4rem 0.6rem',
              borderRadius: 'var(--radius-sm)',
              background: feedbackMsg.includes('Success')
                ? 'rgba(16, 185, 129, 0.15)'
                : 'rgba(239, 68, 68, 0.15)',
              color: feedbackMsg.includes('Success') ? 'var(--emerald-400)' : '#f87171',
            }}
          >
            {feedbackMsg}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <button
            onClick={() => handleAction('accept')}
            disabled={isVerifying || tree.status === 'verified'}
            className="btn btn-primary touch-target"
            style={{ height: 44, minHeight: 44, fontSize: '0.875rem', gap: '0.5rem' }}
          >
            <CheckCircle size={18} />
            <span>Approve</span>
          </button>
          <button
            onClick={() => handleAction('reject')}
            disabled={isVerifying || tree.status === 'rejected'}
            className="btn btn-danger touch-target"
            style={{ height: 44, minHeight: 44, fontSize: '0.875rem', gap: '0.5rem' }}
          >
            <XCircle size={18} />
            <span>Reject</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
