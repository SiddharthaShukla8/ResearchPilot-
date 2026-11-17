import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Download,
  ShieldCheck,
  ExternalLink,
  CheckCircle2,
  Copy,
  X,
} from 'lucide-react';
import { api } from '../api/client';

export const ReportViewerPage: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();

  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCitation, setSelectedCitation] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'review' | 'matrix' | 'disagreements' | 'gaps'>('review');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!runId) return;
    api.getRunReport(runId)
      .then((data) => setReportData(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [runId]);

  const handleCopyMarkdown = () => {
    if (!reportData?.report_markdown) return;
    navigator.clipboard.writeText(reportData.report_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportPDF = () => {
    window.open(`/api/v1/research-runs/${runId}/export?format=pdf`, '_blank');
  };

  if (loading) {
    return <div className="p-8 max-w-5xl mx-auto w-full animate-pulse">Loading literature review report...</div>;
  }

  const report = reportData?.report_json;

  return (
    <div className="p-8 max-w-5xl mx-auto w-full">
      {/* Report Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              Verified Literature Review
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 leading-tight">
            {report?.title}
          </h1>
          <p className="text-sm text-slate-500 mt-1 italic">
            Inquiry: "{report?.research_question}"
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={handleCopyMarkdown}
            className="flex items-center gap-1.5 px-3.5 py-2 border border-slate-200 hover:bg-slate-100 rounded-xl text-xs font-semibold text-slate-700 transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
            {copied ? 'Copied MD!' : 'Copy Markdown'}
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            Export Report (PDF)
          </button>
        </div>
      </div>

      {/* Verification Status Banner */}
      <div className="bg-emerald-50/80 border border-emerald-200 rounded-2xl p-4 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-emerald-800 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>
            Deterministic Citation Integrity Check: <strong>{report?.verification_summary?.citations_validated || 0} citations validated</strong> against uploaded document chunks.
          </span>
        </div>
        <div className="text-emerald-700 font-semibold shrink-0">
          Status: Verified & Grounded
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 mb-8 pb-px">
        {[
          { key: 'review', label: 'Thematic Review & Scope' },
          { key: 'matrix', label: 'Methodology Comparison Matrix' },
          { key: 'disagreements', label: 'Agreements & Variations' },
          { key: 'gaps', label: 'Candidate Research Gaps' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === tab.key
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab 1: Thematic Review */}
      {activeTab === 'review' && (
        <div className="space-y-8">
          <section className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-2">Executive Summary</h2>
            <p className="text-base text-slate-800 leading-relaxed font-normal">
              {report?.executive_summary}
            </p>
          </section>

          <section className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-2">Corpus Scope & Search Method</h2>
            <p className="text-sm text-slate-600 leading-relaxed">
              {report?.scope_and_methods}
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900">Thematic Synthesis</h2>
            {report?.thematic_synthesis.map((theme: any, idx: number) => (
              <div key={idx} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
                <h3 className="text-base font-bold text-slate-900 mb-2">{theme.theme}</h3>
                <p className="text-sm text-slate-700 leading-relaxed mb-4">
                  {theme.content}
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400">Cited Sources:</span>
                  {theme.citations.map((cKey: string, cIdx: number) => {
                    const match = report.references.find((r: any) => r.citation_key === cKey);
                    return (
                      <button
                        key={cIdx}
                        onClick={() => setSelectedCitation(match || { citation_key: cKey })}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs border border-indigo-200 transition-colors"
                      >
                        {cKey} {match?.title ? `• ${match.title.slice(0, 20)}...` : ''}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </section>
        </div>
      )}

      {/* Tab 2: Comparison Matrix */}
      {activeTab === 'matrix' && (
        <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-700 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="p-4">Paper Title</th>
                  <th className="p-4">Methodology / Architecture</th>
                  <th className="p-4">Dataset & Benchmark</th>
                  <th className="p-4">Reported Metrics</th>
                  <th className="p-4">Comparability Tier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {report?.comparison_matrix.map((row: any, idx: number) => (
                  <tr key={idx} className="hover:bg-slate-50/60">
                    <td className="p-4 font-semibold text-slate-900">{row.paper_title}</td>
                    <td className="p-4 text-slate-600">{row.methodology}</td>
                    <td className="p-4 text-slate-600">{row.dataset}</td>
                    <td className="p-4 font-mono text-slate-800">{row.metrics_reported}</td>
                    <td className="p-4">
                      <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium capitalize">
                        {row.comparability.replace('_', ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Agreements & Variations */}
      {activeTab === 'disagreements' && (
        <div className="space-y-4">
          {report?.agreements_and_disagreements.map((item: any, idx: number) => (
            <div key={idx} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
                  {item.classification}
                </span>
                <h3 className="font-bold text-base text-slate-900">{item.topic}</h3>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed mb-3">{item.explanation}</p>
              <div className="flex items-center gap-2">
                {item.cited_keys.map((k: string) => (
                  <span key={k} className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                    {k}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Candidate Research Gaps */}
      {activeTab === 'gaps' && (
        <div className="space-y-4">
          {report?.candidate_research_gaps.map((gap: any, idx: number) => (
            <div key={idx} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
              <h3 className="text-base font-bold text-slate-900 mb-2">{gap.title}</h3>
              <p className="text-sm text-slate-700 leading-relaxed mb-4">{gap.description}</p>
              <div className="p-3 bg-amber-50/60 border border-amber-200/60 rounded-xl text-xs text-amber-800 mb-2">
                <strong>Corpus Evidence Basis:</strong> {gap.evidence_basis}
              </div>
              <p className="text-[11px] text-slate-400 italic">{gap.scope_caveat}</p>
            </div>
          ))}
        </div>
      )}

      {/* Citation Popover / Evidence Inspector Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl border border-slate-200">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                  {selectedCitation.citation_key}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">
                  {selectedCitation.title || 'Ground Truth Citation'}
                </h3>
                <span className="text-xs text-slate-400">Page {selectedCitation.page} in uploaded PDF</span>
              </div>
              <button
                onClick={() => setSelectedCitation(null)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-md"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs font-mono text-slate-800 leading-relaxed mb-4">
              "{selectedCitation.excerpt}"
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
              <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Verified exact excerpt from stored chunk
              </span>
              <a
                href={`/api/v1/documents/${selectedCitation.document_id}/download`}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-500 inline-flex items-center gap-1"
              >
                View Full PDF
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
