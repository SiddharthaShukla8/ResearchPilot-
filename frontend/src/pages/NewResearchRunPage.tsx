import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Sparkles, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import { Document, Project } from '../types';

export const NewResearchRunPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [question, setQuestion] = useState('');
  const [instructions, setInstructions] = useState('');
  const [quickRun, setQuickRun] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    Promise.all([api.getProject(projectId), api.listDocuments(projectId)])
      .then(([proj, docs]) => {
        setProject(proj);
        const readyDocs = docs.filter((d) => d.processing_status === 'ready');
        setDocuments(readyDocs);
        // Default select all ready documents
        setSelectedDocIds(readyDocs.map((d) => d.id));
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  const toggleSelectAll = () => {
    if (selectedDocIds.length === documents.length) {
      setSelectedDocIds([]);
    } else {
      setSelectedDocIds(documents.map((d) => d.id));
    }
  };

  const toggleDoc = (id: string) => {
    if (selectedDocIds.includes(id)) {
      setSelectedDocIds(selectedDocIds.filter((d) => d !== id));
    } else {
      setSelectedDocIds([...selectedDocIds, id]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !question.trim() || selectedDocIds.length === 0) return;
    setSubmitting(true);
    setError(null);

    try {
      const run = await api.createResearchRun(projectId, question, selectedDocIds, quickRun);
      if (quickRun) {
        navigate(`/research-runs/${run.id}/activity`);
      } else {
        navigate(`/research-runs/${run.id}/plan`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to start research run');
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="p-8 max-w-4xl mx-auto w-full animate-pulse">Loading setup...</div>;
  }

  return (
    <div className="p-8 max-w-4xl mx-auto w-full">
      <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
        <Link to={`/projects/${projectId}`} className="hover:text-indigo-600">
          {project?.title || 'Workspace'}
        </Link>
        <span>/</span>
        <span className="text-slate-800 font-medium">New Literature Review</span>
      </div>

      <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-2">
        Start Literature Review Run
      </h1>
      <p className="text-sm text-slate-500 mb-8">
        Ask an academic question across your uploaded papers. The agent will formulate a structured plan, retrieve evidence, and verify all citations.
      </p>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Research Question */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <label className="block text-sm font-bold text-slate-900 mb-1">
            Research Question <span className="text-rose-500">*</span>
          </label>
          <p className="text-xs text-slate-500 mb-3">
            Formulate a clear academic inquiry (e.g. comparing model architectures, benchmark datasets, or performance tradeoffs).
          </p>
          <textarea
            required
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How do Convolutional Neural Networks and Vision Transformers compare in Brain Tumor MRI segmentation accuracy and inference latency?"
            className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
          />
        </div>

        {/* Paper Selection */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Corpus Scope: Select Papers ({selectedDocIds.length}/{documents.length})
              </h3>
              <p className="text-xs text-slate-500">Only verified ready papers will be consulted.</p>
            </div>
            <button
              type="button"
              onClick={toggleSelectAll}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-500"
            >
              {selectedDocIds.length === documents.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {documents.map((doc) => {
              const selected = selectedDocIds.includes(doc.id);
              return (
                <div
                  key={doc.id}
                  onClick={() => toggleDoc(doc.id)}
                  className={`flex items-center justify-between p-3 rounded-xl border text-sm cursor-pointer transition-all ${
                    selected
                      ? 'border-indigo-300 bg-indigo-50/40 text-slate-900'
                      : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className={`w-4 h-4 shrink-0 ${selected ? 'text-indigo-600' : 'text-slate-400'}`} />
                    <span className="truncate font-medium">{doc.title || doc.original_filename}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-400 shrink-0">
                    {doc.publication_year && <span>{doc.publication_year}</span>}
                    <div
                      className={`w-4 h-4 rounded border flex items-center justify-center ${
                        selected ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-slate-300'
                      }`}
                    >
                      {selected && <CheckCircle2 className="w-3.5 h-3.5" />}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Optional Execution Instructions */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <label className="block text-sm font-bold text-slate-900 mb-1">
            Optional Focus Instructions
          </label>
          <input
            type="text"
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="e.g. Focus specifically on Dice score metrics and preprocessing steps..."
            className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 mb-4"
          />

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={quickRun}
              onChange={(e) => setQuickRun(e.target.checked)}
              className="rounded text-indigo-600 focus:ring-indigo-500"
            />
            <span className="text-xs text-slate-700 font-medium">
              Quick Run (auto-approve generated plan and begin execution immediately)
            </span>
          </label>
        </div>

        <div className="flex items-center justify-end gap-3 pt-2">
          <Link
            to={`/projects/${projectId}`}
            className="px-5 py-2.5 border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium text-sm rounded-xl"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting || selectedDocIds.length === 0 || !question.trim()}
            className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm rounded-xl shadow-sm transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            {submitting ? 'Formulating Plan...' : quickRun ? 'Launch Quick Run' : 'Generate & Review Plan'}
          </button>
        </div>
      </form>
    </div>
  );
};
