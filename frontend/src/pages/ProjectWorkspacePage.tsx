import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Upload,
  FileText,
  Trash2,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Download,
} from 'lucide-react';
import { api } from '../api/client';
import { Document, Project } from '../types';

export const ProjectWorkspacePage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();

  const [project, setProject] = useState<Project | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = async () => {
    if (!projectId) return;
    try {
      const [projData, docsData] = await Promise.all([
        api.getProject(projectId),
        api.listDocuments(projectId),
      ]);
      setProject(projData);
      setDocuments(docsData);
    } catch {
      // ignored
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      if (projectId) {
        api.listDocuments(projectId).then((docs) => {
          setDocuments(docs);
        });
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [projectId]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !projectId) return;
    setUploading(true);
    setUploadError(null);

    try {
      const res = await api.uploadDocuments(projectId, Array.from(files));
      if (res.failed.length > 0) {
        setUploadError(`Failed to upload ${res.failed.length} file(s): ${res.failed[0].error}`);
      }
      loadData();
    } catch (err: any) {
      setUploadError(err.message || 'File upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm('Are you sure you want to remove this paper from the workspace?')) return;
    try {
      await api.deleteDocument(docId);
      loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to delete paper');
    }
  };

  const readyDocuments = documents.filter((d) => d.processing_status === 'ready');

  if (loading) {
    return <div className="p-8 max-w-6xl mx-auto w-full animate-pulse">Loading workspace...</div>;
  }

  return (
    <div className="p-8 max-w-6xl mx-auto w-full">
      {/* Workspace Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
            <Link to="/dashboard" className="hover:text-indigo-600 transition-colors">Workspaces</Link>
            <span>/</span>
            <span className="text-slate-800 font-medium">{project?.title}</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{project?.title}</h1>
          <p className="text-sm text-slate-500 mt-1">{project?.description || 'No description provided.'}</p>
        </div>

        <Link
          to={`/projects/${projectId}/new-run`}
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm shadow-sm transition-all ${
            readyDocuments.length > 0
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-200'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
          onClick={(e) => {
            if (readyDocuments.length === 0) e.preventDefault();
          }}
        >
          <Sparkles className="w-4 h-4" />
          Start Literature Review
          <ArrowRight className="w-4 h-4 ml-1" />
        </Link>
      </div>

      {uploadError && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {uploadError}
        </div>
      )}

      {/* Upload Dropzone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFileUpload(e.dataTransfer.files);
        }}
        className="mb-8 border-2 border-dashed border-slate-200 hover:border-indigo-400 bg-white hover:bg-indigo-50/20 rounded-2xl p-8 text-center cursor-pointer transition-all"
      >
        <input
          type="file"
          ref={fileInputRef}
          multiple
          accept=".pdf"
          className="hidden"
          onChange={(e) => handleFileUpload(e.target.files)}
        />
        <div className="w-12 h-12 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
          <Upload className="w-6 h-6" />
        </div>
        <h3 className="font-semibold text-base text-slate-800 mb-1">
          {uploading ? 'Processing uploaded files...' : 'Upload Academic Research Papers (PDF)'}
        </h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
          Drag and drop PDF files here, or click to browse. Max 25 MB per PDF. Extraction preserves 1-based page coordinates.
        </p>
      </div>

      {/* Papers Library */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            Paper Library
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              {documents.length}
            </span>
          </h2>
        </div>

        {documents.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-sm text-slate-400">
            No papers uploaded yet. Add academic papers to begin literature synthesis.
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
            <div className="divide-y divide-slate-100">
              {documents.map((doc) => (
                <div key={doc.id} className="p-4 flex items-center justify-between gap-4 hover:bg-slate-50/60 transition-colors">
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 shrink-0">
                      <FileText className="w-5 h-5 text-indigo-600" />
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-sm font-semibold text-slate-900 truncate">
                        {doc.title || doc.original_filename}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-slate-400 mt-0.5">
                        <span>{(doc.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                        {doc.page_count > 0 && <span>• {doc.page_count} pages</span>}
                        {doc.publication_year && <span>• Year: {doc.publication_year}</span>}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {doc.processing_status === 'ready' ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Ready
                      </span>
                    ) : doc.processing_status === 'failed' ? (
                      <span
                        title={doc.processing_error || 'Failed'}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200"
                      >
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Failed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 animate-pulse">
                        <Clock className="w-3.5 h-3.5" />
                        {doc.processing_status}
                      </span>
                    )}

                    <a
                      href={`/api/v1/documents/${doc.id}/download`}
                      download={doc.original_filename}
                      className="p-1.5 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-100"
                      title="Download PDF"
                    >
                      <Download className="w-4 h-4" />
                    </a>

                    <button
                      onClick={() => handleDeleteDoc(doc.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md hover:bg-rose-50"
                      title="Delete Paper"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
