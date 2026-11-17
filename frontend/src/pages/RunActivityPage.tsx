import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { CheckCircle2, Clock, ArrowRight, FileText, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import { AgentEvent, ResearchRun } from '../types';

export const RunActivityPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();

  const [run, setRun] = useState<ResearchRun | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    if (!runId) return;
    try {
      const [runData, eventsData] = await Promise.all([
        api.getResearchRun(runId),
        api.getRunEvents(runId),
      ]);
      setRun(runData);
      setEvents(eventsData);

      if (runData.status === 'completed') {
        navigate(`/research-runs/${runId}/report`, { replace: true });
      }
    } catch {
      // ignored
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2500);
    return () => clearInterval(interval);
  }, [runId]);

  if (loading) {
    return <div className="p-8 max-w-4xl mx-auto w-full animate-pulse">Loading activity timeline...</div>;
  }

  const stages = [
    { key: 'queued', label: 'Queued' },
    { key: 'retrieving', label: 'Retrieval' },
    { key: 'analysing', label: 'Paper Analysis' },
    { key: 'synthesising', label: 'Synthesis' },
    { key: 'verifying', label: 'Citation Verification' },
    { key: 'completed', label: 'Complete' },
  ];

  const currentStageIndex = stages.findIndex((s) => s.key === run?.status);

  return (
    <div className="p-8 max-w-4xl mx-auto w-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
            Phase 2: Execution & Provenance
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-2">
            Research Orchestrator Activity
          </h1>
          <p className="text-sm text-slate-500 mt-0.5 line-clamp-1">
            Question: "{run?.research_question}"
          </p>
        </div>

        {run?.status === 'completed' && (
          <Link
            to={`/research-runs/${runId}/report`}
            className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold shadow-sm transition-all"
          >
            <FileText className="w-4 h-4" />
            View Review Report
            <ArrowRight className="w-4 h-4" />
          </Link>
        )}
      </div>

      {/* Stepper Progress Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm mb-8">
        <div className="flex items-center justify-between relative">
          {stages.map((stage, idx) => {
            const isDone = currentStageIndex > idx || run?.status === 'completed';
            const isCurrent = run?.status === stage.key;

            return (
              <div key={stage.key} className="flex flex-col items-center z-10 flex-1">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition-all ${
                    isDone
                      ? 'bg-emerald-600 text-white'
                      : isCurrent
                      ? 'bg-indigo-600 text-white ring-4 ring-indigo-100 animate-pulse'
                      : 'bg-slate-100 text-slate-400'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    idx + 1
                  )}
                </div>
                <span
                  className={`text-[11px] font-medium mt-2 text-center ${
                    isDone || isCurrent ? 'text-slate-900 font-semibold' : 'text-slate-400'
                  }`}
                >
                  {stage.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Timeline Event Log */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-400" />
          Operational Timeline
        </h3>

        {events.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400">Waiting for agent worker to claim job...</div>
        ) : (
          <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100">
            {events.map((ev) => (
              <div key={ev.id} className="relative group">
                <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-indigo-500 ring-4 ring-white"></div>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 block mb-0.5">
                      {ev.event_type.replace('_', ' ')}
                    </span>
                    <p className="text-sm text-slate-800 leading-snug">{ev.safe_summary}</p>
                  </div>
                  <span className="text-[11px] text-slate-400 shrink-0">
                    {new Date(ev.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
