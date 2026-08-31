export type ApplicationStatus =
  | 'discovered'
  | 'applied'
  | 'responded'
  | 'interview_scheduled'
  | 'offer'
  | 'rejected'
  | 'ghosted';

export interface TimelineEntry {
  date: string;
  event: string;
  notes?: string | null;
}

export interface Application {
  id: string;
  company: string;
  role: string;
  job_url?: string | null;
  location?: string | null;
  salary_range?: string | null;
  jd_snapshot?: string | null;
  status: ApplicationStatus;
  relevance_score?: number | null;
  notes?: string | null;
  tags: string[];
  resume_filename?: string | null;
  resume_text?: string | null;
  tailored_resume_summary?: string | null;
  tailored_bullets?: string[];
  matched_skills?: string[];
  missing_skills?: string[];
  date_discovered: string;
  date_applied?: string | null;
  interview_date?: string | null;
  resume_version_id?: string | null;
  prep_doc_id?: string | null;
  timeline: TimelineEntry[];
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreate {
  company: string;
  role: string;
  job_url?: string | null;
  location?: string | null;
  salary_range?: string | null;
  jd_snapshot?: string | null;
  status?: ApplicationStatus;
  relevance_score?: number | null;
  notes?: string | null;
  tags?: string[];
}

export interface ApplicationUpdate {
  company?: string;
  role?: string;
  job_url?: string | null;
  location?: string | null;
  salary_range?: string | null;
  jd_snapshot?: string | null;
  status?: ApplicationStatus;
  relevance_score?: number | null;
  notes?: string | null;
  tags?: string[];
  interview_date?: string | null;
}

export interface ApplicationStats {
  total_applications: number;
  by_status: Record<ApplicationStatus, number>;
  active_pipeline: number;
}
