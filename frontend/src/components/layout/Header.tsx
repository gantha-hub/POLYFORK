import React, { useState } from 'react';
import { useProject } from '../../context/ProjectContext';
import { api } from '../../api/client';
import { Modal } from '../common/Modal';
import { TreePine, Plus, Layers, FolderKanban } from 'lucide-react';

export const Header: React.FC = () => {
  const {
    health,
    projects,
    activeProject,
    setActiveProject,
    surveys,
    activeSurvey,
    setActiveSurvey,
    refreshProjects,
  } = useProject();

  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const res = await api.createProject({
        name: newProjectName.trim(),
        description: newProjectDesc.trim() || undefined,
      });
      await refreshProjects();
      setActiveProject(res.data);
      setIsNewProjectModalOpen(false);
      setNewProjectName('');
      setNewProjectDesc('');
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <header
        style={{
          height: '60px',
          background: 'var(--bg-header)',
          backdropFilter: 'var(--backdrop-blur)',
          WebkitBackdropFilter: 'var(--backdrop-blur)',
          borderBottom: '1px solid var(--border-subtle)',
          padding: '0 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          zIndex: 100,
        }}
      >
        {/* Brand Logo & Name */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 'var(--radius-md)',
              background: 'var(--forest-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px var(--forest-glow)',
            }}
          >
            <TreePine size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ fontWeight: 800, fontSize: '1.05rem', letterSpacing: '-0.02em', color: '#ffffff' }}>
                VrikshaVision
              </span>
              <span
                className="font-mono"
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  color: 'var(--emerald-400)',
                  background: 'rgba(16, 185, 129, 0.12)',
                  padding: '0.1rem 0.4rem',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(16, 185, 129, 0.25)',
                }}
              >
                TWIN v1.0
              </span>
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              Forest Canopy Digital Twin & Biomass Observatory
            </div>
          </div>
        </div>

        {/* Global Project & Survey Switchers */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          {/* Desktop Selectors (hidden on mobile) */}
          <div className="hide-on-mobile" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            {/* Project Picker */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <FolderKanban size={15} style={{ color: 'var(--text-muted)' }} />
              <select
                aria-label="Active Forestry Project"
                className="input-field"
                style={{
                  width: 180,
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.8rem',
                  height: 34,
                }}
                value={activeProject?.id || ''}
                onChange={(e) => {
                  const found = projects.find((p) => p.id === e.target.value);
                  if (found) setActiveProject(found);
                }}
              >
                {projects.length === 0 ? (
                  <option value="">No projects found</option>
                ) : (
                  projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))
                )}
              </select>

              <button
                onClick={() => setIsNewProjectModalOpen(true)}
                className="btn btn-secondary btn-sm"
                title="Create new forestry project"
                style={{ height: 34, padding: '0 0.6rem' }}
              >
                <Plus size={14} />
              </button>
            </div>

            {/* Active Survey Selector */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Layers size={15} style={{ color: 'var(--text-muted)' }} />
              <select
                aria-label="Active Aerial Survey"
                className="input-field"
                style={{
                  width: 200,
                  padding: '0.35rem 0.75rem',
                  fontSize: '0.8rem',
                  height: 34,
                }}
                value={activeSurvey?.id || ''}
                onChange={(e) => {
                  const found = surveys.find((s) => s.id === e.target.value);
                  if (found) setActiveSurvey(found);
                }}
                disabled={surveys.length === 0}
              >
                {surveys.length === 0 ? (
                  <option value="">No surveys uploaded</option>
                ) : (
                  surveys.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.original_filename} ({s.forest_type})
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          {/* Mobile Compact Project/Survey Pill (shown only on mobile) */}
          <button
            onClick={() => setIsNewProjectModalOpen(true)}
            className="hide-on-desktop touch-target"
            style={{
              padding: '0.3rem 0.65rem',
              borderRadius: 'var(--radius-pill)',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid var(--border-card)',
              color: 'var(--emerald-400)',
              fontSize: '0.75rem',
              fontWeight: 600,
              gap: '0.35rem',
              cursor: 'pointer',
            }}
          >
            <FolderKanban size={13} />
            <span style={{ maxWidth: 110, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {activeProject ? activeProject.name : 'Select Stand'}
            </span>
          </button>

          {/* Backend Diagnostics Pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              padding: '0.3rem 0.65rem',
              borderRadius: 'var(--radius-pill)',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.72rem',
            }}
          >
            <span className="pulse-indicator" style={{ backgroundColor: health ? 'var(--emerald-400)' : '#ef4444' }} />
            <span style={{ color: health ? 'var(--text-secondary)' : '#f87171', fontWeight: 600 }}>
              {health ? (health.model_backend === 'mock' ? 'MOCK' : 'GPU') : 'OFFLINE'}
            </span>
          </div>
        </div>
      </header>

      {/* New Project Modal */}
      <Modal
        isOpen={isNewProjectModalOpen}
        onClose={() => setIsNewProjectModalOpen(false)}
        title="Create Forestry Project"
      >
        <form onSubmit={handleCreateProject} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Project Name *
            </label>
            <input
              type="text"
              required
              className="input-field"
              placeholder="e.g. Western Ghats Stand A"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
              Description (Optional)
            </label>
            <textarea
              className="input-field"
              rows={3}
              placeholder="e.g. High resolution UAV canopy survey for carbon baseline"
              value={newProjectDesc}
              onChange={(e) => setNewProjectDesc(e.target.value)}
            />
          </div>

          {errorMsg && (
            <div style={{ color: '#f87171', fontSize: '0.8rem', padding: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 'var(--radius-sm)' }}>
              {errorMsg}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setIsNewProjectModalOpen(false)}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting || !newProjectName.trim()}
            >
              {isSubmitting ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </Modal>
    </>
  );
};
