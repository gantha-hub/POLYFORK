import React, { useEffect, useState } from 'react';
import { useProject } from '../context/ProjectContext';
import { api } from '../api/client';
import type { TreeQueueItem } from '../types/api';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import {
  CheckCircle,
  XCircle,
  Edit3,
  Loader2,
  TreePine,
  Layers,
} from 'lucide-react';

export const VerifyPage: React.FC = () => {
  const { activeSurvey } = useProject();

  const [queue, setQueue] = useState<TreeQueueItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Edit Modal State
  const [editingTree, setEditingTree] = useState<TreeQueueItem | null>(null);
  const [editNotes, setEditNotes] = useState('');
  const [submittingAction, setSubmittingAction] = useState<string | null>(null);

  const fetchQueue = () => {
    if (!activeSurvey) return;
    setLoading(true);
    setError(null);
    api.getVerificationQueue(activeSurvey.id)
      .then((res) => {
        setQueue(res.data);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load verification queue');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchQueue();
  }, [activeSurvey]);

  const handleAction = async (treeId: string, action: 'accept' | 'reject' | 'edit', notes?: string) => {
    setSubmittingAction(treeId);
    try {
      await api.submitVerification({
        tree_id: treeId,
        action,
        user_id: 'forester_auditor',
        notes: notes || `Audited from verification queue as ${action}`,
      });

      // Update local item status
      setQueue((prev) =>
        prev.map((item) =>
          item.tree_id === treeId
            ? { ...item, status: action === 'accept' ? 'verified' : action === 'reject' ? 'rejected' : 'edited' }
            : item
        )
      );

      if (editingTree?.tree_id === treeId) {
        setEditingTree(null);
        setEditNotes('');
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setSubmittingAction(null);
    }
  };

  const verifiedCount = queue.filter((t) => t.status === 'verified' || t.status === 'rejected' || t.status === 'edited').length;
  const progressPercent = queue.length > 0 ? Math.round((verifiedCount / queue.length) * 100) : 0;

  if (!activeSurvey) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
        <Layers size={40} style={{ marginBottom: '1rem', opacity: 0.5 }} />
        <h2>No Active Survey Selected</h2>
        <p style={{ fontSize: '0.85rem' }}>Select an aerial survey in the top navigation bar to audit tree crowns.</p>
      </div>
    );
  }

  return (
    <div className="page-responsive-container">
      {/* Page Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.35rem' }}>
          Active Learning & Human-in-the-Loop Audit Queue
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          Prioritizes tree crown detections with highest conformal epistemic uncertainty, low segmentation confidence, or boundary anomalies for verified forester auditing.
        </p>
      </div>

      {/* Progress & Queue Health Banner */}
      <div
        className="glass-card"
        style={{
          padding: '1.25rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Audit Completion Progress</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ffffff', marginTop: '0.2rem' }}>
            {verifiedCount} of {queue.length} crowns reviewed ({progressPercent}%)
          </div>
        </div>

        <div style={{ width: 280, display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
          <div
            style={{
              height: 8,
              borderRadius: 'var(--radius-pill)',
              background: 'rgba(255, 255, 255, 0.08)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${progressPercent}%`,
                height: '100%',
                background: 'var(--forest-gradient)',
                borderRadius: 'var(--radius-pill)',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            <span>Target: 100% Quality Assurance</span>
            <span>{queue.length - verifiedCount} remaining</span>
          </div>
        </div>
      </div>

      {/* Error or Loading */}
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, gap: '0.75rem' }}>
          <Loader2 size={24} color="var(--emerald-400)" className="animate-spin" />
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Calculating uncertainty queue...</span>
        </div>
      )}

      {error && (
        <div
          style={{
            padding: '1rem',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.15)',
            color: '#f87171',
            fontSize: '0.85rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Queue Grid Cards */}
      {!loading && !error && queue.length === 0 && (
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <CheckCircle size={40} color="var(--emerald-400)" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ color: '#ffffff', marginBottom: '0.5rem' }}>Audit Queue Empty</h3>
          <p style={{ fontSize: '0.85rem' }}>All tree canopy crowns in this survey meet high-confidence certification thresholds.</p>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 320px), 1fr))', gap: '1.25rem' }}>
        {queue.map((item) => {
          const isDone = item.status === 'verified' || item.status === 'rejected' || item.status === 'edited';
          return (
            <div
              key={item.tree_id}
              className="glass-card"
              style={{
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
                opacity: isDone ? 0.65 : 1,
                border: item.priority_score > 0.7 && !isDone
                  ? '1px solid rgba(245, 158, 11, 0.5)'
                  : '1px solid var(--border-card)',
              }}
            >
              {/* Card Header */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <TreePine size={18} color={isDone ? 'var(--emerald-400)' : '#f59e0b'} />
                  <div>
                    <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff' }}>
                      Tree #{item.tree_id.slice(-6)}
                    </h3>
                    <span className="font-mono" style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>
                      {item.tree_id}
                    </span>
                  </div>
                </div>

                <Badge
                  variant={
                    item.status === 'verified'
                      ? 'calibrated'
                      : item.status === 'rejected'
                      ? 'danger'
                      : 'uncalibrated'
                  }
                  label={item.status.toUpperCase()}
                />
              </div>

              {/* Priority & Reason */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255, 255, 255, 0.02)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-md)' }}>
                <div>
                  <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>Uncertainty Priority</div>
                  <div className="font-mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f59e0b' }}>
                    {(item.priority_score * 100).toFixed(0)}%
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>Audit Reason</div>
                  <span
                    style={{
                      fontSize: '0.725rem',
                      fontWeight: 600,
                      color: 'var(--text-secondary)',
                      textTransform: 'capitalize',
                    }}
                  >
                    {item.audit_reason.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>

              {/* Geometry Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.75rem' }}>
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Crown Area: </span>
                  <strong style={{ color: '#ffffff' }}>{item.crown_area_sqm.toFixed(1)} m²</strong>
                </div>
                <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.4rem 0.6rem', borderRadius: 'var(--radius-sm)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Model Conf: </span>
                  <strong style={{ color: '#ffffff' }}>{(item.confidence * 100).toFixed(1)}%</strong>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.5rem', marginTop: 'auto' }}>
                <button
                  onClick={() => handleAction(item.tree_id, 'accept')}
                  disabled={submittingAction === item.tree_id || item.status === 'verified'}
                  className="btn btn-primary touch-target"
                  style={{ gap: '0.35rem', height: 38, minHeight: 38, fontSize: '0.8rem' }}
                >
                  <CheckCircle size={15} />
                  <span>Approve</span>
                </button>

                <button
                  onClick={() => handleAction(item.tree_id, 'reject')}
                  disabled={submittingAction === item.tree_id || item.status === 'rejected'}
                  className="btn btn-danger touch-target"
                  style={{ gap: '0.35rem', height: 38, minHeight: 38, fontSize: '0.8rem' }}
                >
                  <XCircle size={15} />
                  <span>Reject</span>
                </button>

                <button
                  onClick={() => {
                    setEditingTree(item);
                    setEditNotes('');
                  }}
                  className="btn btn-secondary touch-target"
                  title="Edit notes / attributes"
                  aria-label="Edit audit notes"
                  style={{ width: 38, height: 38, minHeight: 38, padding: 0 }}
                >
                  <Edit3 size={15} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Edit Crown Modal */}
      <Modal
        isOpen={!!editingTree}
        onClose={() => setEditingTree(null)}
        title={`Audit Notes for Tree #${editingTree?.tree_id.slice(-6)}`}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Field Auditor Observations / Calibrated Notes
            </label>
            <textarea
              className="input-field"
              rows={4}
              placeholder="e.g. Stem diameter measured manually as 28.4 cm. Crown overlaps with neighboring canopy."
              value={editNotes}
              onChange={(e) => setEditNotes(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button
              onClick={() => setEditingTree(null)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={() => editingTree && handleAction(editingTree.tree_id, 'edit', editNotes)}
              className="btn btn-primary"
              disabled={submittingAction === editingTree?.tree_id}
            >
              Save Audit Record
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
