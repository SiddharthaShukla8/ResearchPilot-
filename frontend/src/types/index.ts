export interface User {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Project {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  document_count: number;
}

export interface Document {
  id: string;
  project_id: string;
  owner_id: string;
  original_filename: string;
  sha256: string;
  file_size: number;
  page_count: number;
  title: string | null;
  authors: string[] | null;
  publication_year: number | null;
  doi: string | null;
  processing_status: 'uploaded' | 'queued' | 'extracting' | 'chunking' | 'embedding' | 'indexing' | 'ready' | 'failed';
  processing_error: string | null;
  created_at: string;
  processed_at: string | null;
}

export interface PlanStep {
  step_order: number;
  step_type: 'retrieval' | 'analysis' | 'comparison' | 'synthesis' | 'verification';
  title: string;
  instructions: string;
}

export interface ResearchPlan {
  objective: string;
  sub_questions: string[];
  steps: PlanStep[];
  comparison_dimensions: string[];
  expected_sections: string[];
}

export interface AgentEvent {
  id: string;
  run_id: string;
  sequence: number;
  event_type: string;
  safe_summary: string;
  metadata_json: Record<string, any> | null;
  created_at: string;
}

export interface ResearchRun {
  id: string;
  project_id: string;
  owner_id: string;
  research_question: string;
  selected_document_ids: string[];
  citation_style: string;
  status: 'queued' | 'planning' | 'awaiting_approval' | 'retrieving' | 'analysing' | 'synthesising' | 'verifying' | 'completed' | 'failed' | 'cancelled';
  plan_json: ResearchPlan | null;
  report_json: any | null;
  report_markdown: string | null;
  error_code: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}
