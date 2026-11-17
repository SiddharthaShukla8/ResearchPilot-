import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Play, AlertCircle, X } from 'lucide-react';
import { api } from '../api/client';
import { ResearchPlan, ResearchRun } from '../types';

export const PlanReviewPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();

  const [run, setRun] = useState<ResearchRun | null>(null);
  const [plan, setPlan] = useState<ResearchPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    api.getResearchRun(runId)
      .then((data) => {
        setRun(data);
        setPlan(data.plan_json);
        if (data.status !== 'awaiting_approval') {
          navigate(`/research-runs/${runId}/activity`, { replace: true });
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [runId, navigate]);

  const handleApprove = async () => {
    if (!runId) return;
    setApproving(true);
    try {
      await api.approvePlan(runId);
      navigate(`/research-runs/${runId}/activity`);
    } catch (err: any) {
      setError(err.message || 'Approval failed');
      setApproving(false);
    }
  };

  const handleCancel = async () => {
    if (!runId) return;
    if (!confirm('Are you sure you want to cancel this literature review run?')) return;
    setCancelling(true);
    try {
      await api.cancelRun(runId);
      navigate(`/projects/${run?.project_id}`);
    } catch (err: any) {
      setError(err.message || 'Cancel failed');
      setCancelling(false);
    }
  };

  if (loading) {
    return <div className="p-8 max-w-4xl mx-auto w-full animate-pulse">Loading research plan...</div>;
  }

  return (
    <div className="p-8 max-w-4xl mx-auto w-full">
      <div className="flex items-center justify-between mb-6">
        <div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
            Phase 1: Plan Review
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-2">
            Inspect & Approve Research Plan
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            The Agent Planner has decomposed your inquiry into verifiable sub-questions and retrieval steps.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="flex items-center gap-1.5 px-4 py-2 border border-slate-200 text-slate-600 hover:bg-slate-100 rounded-xl text-sm font-medium transition-colors"
          >
            <X className="w-4 h-4" />
            Cancel Run
          </button>
          <button
            onClick={handleApprove}
            disabled={approving}
            className="flex items-center gap-2 px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-sm transition-all"
          >
            <Play className="w-4 h-4 fill-white" />
            {approving ? 'Starting Execution...' : 'Approve & Run Agent'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Plan Details */}
      <div className="space-y-6">
        {/* Objective */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Research Objective</h3>
          <p className="text-base font-semibold text-slate-900">{plan?.objective}</p>
        </div>

        {/* Sub-questions */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Target Sub-Questions</h3>
          <div className="space-y-2.5">
            {plan?.sub_questions.map((q, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-sm text-slate-800">
                <span className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span className="leading-snug">{q}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Planned Steps */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Bounded Execution Steps</h3>
          <div className="space-y-3">
            {plan?.steps.map((s, idx) => (
              <div key={idx} className="p-4 rounded-xl border border-slate-200 flex items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 capitalize">
                      {s.step_type}
                    </span>
                    <h4 className="text-sm font-semibold text-slate-900">{s.title}</h4>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{s.instructions}</p>
                </div>
                <span className="text-xs font-medium text-slate-400 shrink-0">Step {s.step_order}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Expected Sections */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Comparison Dimensions</h3>
            <ul className="space-y-1.5 text-xs text-slate-600">
              {plan?.comparison_dimensions.map((dim, idx) => (
                <li key={idx} className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                  {dim}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Report Structure Sections</h3>
            <ul className="space-y-1.5 text-xs text-slate-600">
              {plan?.expected_sections.map((sec, idx) => (
                <li key={idx} className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  {sec}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
