import { AuthTokens, Document, Project, ResearchRun, AgentEvent, User } from '../types';

const API_BASE = '/api/v1';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('rp_access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = 'An unexpected error occurred';
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // ignored
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Auth
  async register(name: string, email: string, password: string): Promise<AuthTokens> {
    const data = await request<AuthTokens>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
    localStorage.setItem('rp_access_token', data.access_token);
    localStorage.setItem('rp_refresh_token', data.refresh_token);
    return data;
  },

  async login(email: string, password: string): Promise<AuthTokens> {
    const data = await request<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('rp_access_token', data.access_token);
    localStorage.setItem('rp_refresh_token', data.refresh_token);
    return data;
  },

  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },

  logout(): void {
    localStorage.removeItem('rp_access_token');
    localStorage.removeItem('rp_refresh_token');
  },

  // Projects
  async listProjects(): Promise<Project[]> {
    return request<Project[]>('/projects');
  },

  async createProject(title: string, description?: string): Promise<Project> {
    return request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    });
  },

  async getProject(projectId: string): Promise<Project> {
    return request<Project>(`/projects/${projectId}`);
  },

  async deleteProject(projectId: string): Promise<void> {
    return request<void>(`/projects/${projectId}`, { method: 'DELETE' });
  },

  // Documents
  async listDocuments(projectId: string): Promise<Document[]> {
    return request<Document[]>(`/projects/${projectId}/documents`);
  },

  async uploadDocuments(projectId: string, files: File[]): Promise<{ uploaded: Document[]; duplicates: string[]; failed: any[] }> {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));

    const token = localStorage.getItem('rp_access_token');
    const res = await fetch(`${API_BASE}/projects/${projectId}/documents`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!res.ok) {
      throw new Error('Upload failed');
    }
    return res.json();
  },

  async deleteDocument(documentId: string): Promise<void> {
    return request<void>(`/documents/${documentId}`, { method: 'DELETE' });
  },

  // Research Runs
  async createResearchRun(
    projectId: string,
    question: string,
    selectedDocumentIds: string[],
    quickRun: boolean = false
  ): Promise<ResearchRun> {
    return request<ResearchRun>(`/projects/${projectId}/research-runs`, {
      method: 'POST',
      body: JSON.stringify({
        research_question: question,
        selected_document_ids: selectedDocumentIds,
        quick_run: quickRun,
      }),
    });
  },

  async getResearchRun(runId: string): Promise<ResearchRun> {
    return request<ResearchRun>(`/research-runs/${runId}`);
  },

  async approvePlan(runId: string): Promise<ResearchRun> {
    return request<ResearchRun>(`/research-runs/${runId}/approve`, { method: 'POST' });
  },

  async cancelRun(runId: string): Promise<ResearchRun> {
    return request<ResearchRun>(`/research-runs/${runId}/cancel`, { method: 'POST' });
  },

  async getRunEvents(runId: string): Promise<AgentEvent[]> {
    return request<AgentEvent[]>(`/research-runs/${runId}/events`);
  },

  async getRunReport(runId: string): Promise<{ report_json: any; report_markdown: string }> {
    return request<{ report_json: any; report_markdown: string }>(`/research-runs/${runId}/report`);
  },

  async getChunkEvidence(chunkId: string): Promise<any> {
    return request<any>(`/retrieval/evidence/chunk/${chunkId}`);
  },

  async downloadRunExport(runId: string, format: 'pdf' | 'markdown'): Promise<Blob> {
    const token = localStorage.getItem('rp_access_token');
    const res = await fetch(`${API_BASE}/research-runs/${runId}/export?format=${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      throw new Error('Export download failed');
    }
    return res.blob();
  },
};
