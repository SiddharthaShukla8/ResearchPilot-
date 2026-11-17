import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, BookCheck, FileText, Layers, ShieldCheck, Sparkles } from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-900 text-white selection:bg-indigo-500 selection:text-white">
      {/* Header */}
      <header className="border-b border-slate-800 backdrop-blur-sm sticky top-0 z-50 bg-slate-900/80">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center font-bold">
              <BookCheck className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">ResearchPilot</span>
          </div>

          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-all shadow-sm shadow-indigo-500/20"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-24 px-6 max-w-4xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-950/80 border border-indigo-800/60 text-indigo-300 text-xs font-semibold mb-8">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          Autonomous Literature Synthesis with Provenance Verification
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white mb-6 leading-tight">
          Turn research papers into <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-sky-300 to-indigo-200">
            evidence-backed literature reviews.
          </span>
        </h1>

        <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Upload academic PDFs, inspect an AI-generated research plan, and orchestrate a multi-step agent workflow.
          Every synthesized claim is deterministically linked to real pages and excerpts.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/register"
            className="w-full sm:w-auto flex items-center justify-center gap-2 text-base font-semibold bg-indigo-600 hover:bg-indigo-500 text-white px-7 py-3 rounded-xl transition-all shadow-lg shadow-indigo-600/30"
          >
            Start Literature Review
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/login"
            className="w-full sm:w-auto flex items-center justify-center text-base font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 px-7 py-3 rounded-xl border border-slate-700 transition-all"
          >
            Sign In to Workspace
          </Link>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 px-6 max-w-5xl mx-auto border-t border-slate-800">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl bg-slate-800/40 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-indigo-950 border border-indigo-800 flex items-center justify-center text-indigo-400 mb-4">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-lg text-white mb-2">Page-Aware Ingestion</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              PyMuPDF extraction preserves 1-based page mappings. Chunks maintain accurate provenance back to source text.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-800/40 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-indigo-950 border border-indigo-800 flex items-center justify-center text-indigo-400 mb-4">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-lg text-white mb-2">Hybrid Rank Fusion</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              pgvector dense similarity combined with PostgreSQL full-text keyword retrieval via Reciprocal Rank Fusion.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-800/40 border border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-indigo-950 border border-indigo-800 flex items-center justify-center text-indigo-400 mb-4">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-lg text-white mb-2">Zero-Hallucination Guard</h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              Deterministic citation verification verifies excerpts exist in real chunks. Unsupported claims are removed or flagged.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
