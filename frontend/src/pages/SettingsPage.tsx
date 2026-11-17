import React from 'react';
import { ShieldCheck, Sliders, User, Info } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="p-8 max-w-4xl mx-auto w-full">
      <h1 className="text-2xl font-bold tracking-tight text-slate-900 mb-1">System & Account Settings</h1>
      <p className="text-sm text-slate-500 mb-8">Manage your profile, verified privacy parameters, and model configuration.</p>

      <div className="space-y-6">
        {/* User Profile */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Researcher Profile</h2>
              <p className="text-xs text-slate-400">Authenticated user identity</p>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="font-semibold text-slate-500 block mb-1">Full Name</span>
              <span className="text-slate-900 font-medium text-sm">{user?.name}</span>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="font-semibold text-slate-500 block mb-1">Academic Email</span>
              <span className="text-slate-900 font-medium text-sm">{user?.email}</span>
            </div>
          </div>
        </div>

        {/* Model and Retrieval Configuration */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Model & Engine Configuration</h2>
              <p className="text-xs text-slate-400">Parameters controlling synthesis and embedding generation</p>
            </div>
          </div>

          <div className="grid sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="font-semibold text-slate-500 block mb-1">Synthesis Model</span>
              <span className="text-slate-900 font-medium">gpt-4o-mini (Configured)</span>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="font-semibold text-slate-500 block mb-1">Embedding Engine</span>
              <span className="text-slate-900 font-medium">text-embedding-3-small (1536d)</span>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="font-semibold text-slate-500 block mb-1">Retrieval Fusion</span>
              <span className="text-slate-900 font-medium">pgvector + tsvector (RRF k=60)</span>
            </div>
          </div>
        </div>

        {/* Privacy & Provenance Guarantee */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Privacy & Provenance Notice</h2>
              <p className="text-xs text-slate-400">Academic rigor and privacy safeguards</p>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed mb-4">
            ResearchPilot is architected with strict citation integrity. Uploaded papers are stored securely and parsed into page-indexed embeddings.
            When an external AI provider (such as OpenAI) is configured via environment variables, document chunk excerpts are securely transmitted for embedding generation and report synthesis.
            The system performs deterministic verification to ensure no papers, quotes, or citations are fabricated.
          </p>

          <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-2.5 text-xs text-slate-600">
            <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <span>
              All data is strictly user-scoped. Documents and projects are isolated by authenticated user IDs, and private files cannot be accessed across accounts.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
