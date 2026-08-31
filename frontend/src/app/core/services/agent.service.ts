import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface AIModel {
  id: string;
  name: string;
  provider: string;
  configured: boolean;
  speed: string;
  tier: string;
}

export interface MatchCheckResult {
  ats_score?: number;
  ats_rating?: string;
  match_percentage: number;
  verdict: string;
  role_alignment_summary?: string;
  required_skills?: string[];
  optional_skills?: string[];
  matched_skills: string[];
  missing_critical_keywords?: string[];
  missing_skills: string[];
  necessary_changes?: string[];
  strengths_summary?: string;
  talking_points: string[];
  tailored_bullets?: string[];
  preparation_roadmap: string[];
  model_used: string;
  filename?: string;
  extracted_resume_preview?: string;
}

export interface CareerSite {
  name: string;
  type: string;
  identifier: string;
}

export interface DSAQuestion {
  title: string;
  difficulty: string;
  topic: string;
  frequency: string;
  hint: string;
  leetcode_url?: string;
  neetcode_url?: string;
  time_complexity?: string;
  space_complexity?: string;
}

export interface RedditExperience {
  source: string;
  title: string;
  url?: string;
  summary: string;
  tips: string;
}

export interface InterviewPrepResult {
  company: string;
  role: string;
  dsa_questions: DSAQuestion[];
  system_design_topics: string[];
  technical_deep_dives: string[];
  behavioral_questions: { question: string; focus: string; star_tip: string }[];
  reddit_experiences?: RedditExperience[];
  interview_format: string;
  model_used: string;
}

export interface DiscoveredJob {
  id: string;
  company: string;
  role: string;
  location: string;
  salary_range?: string | null;
  min_experience?: string | null;
  job_url?: string | null;
  source: string;
  tags: string[];
  jd_snapshot: string;
  extracted_skills: string[];
  relevance_score: number;
  tracked?: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class AgentService {
  private baseUrl = `${environment.apiBaseUrl}/agent`;

  selectedModel = signal<string>('gemini-3.7-flash');
  availableModels = signal<AIModel[]>([]);
  activeDefault = signal<string>('gemini-3.7-flash');
  careerSites = signal<CareerSite[]>([]);

  constructor(private http: HttpClient) {}

  loadModels(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/models`).pipe(
      tap((res) => {
        if (res.models) {
          this.availableModels.set(res.models);
          this.activeDefault.set(res.active_default || 'gemini-3.7-flash');
          if (!this.selectedModel()) {
            this.selectedModel.set(res.active_default || 'gemini-3.7-flash');
          }
        }
      })
    );
  }

  checkMatch(payload: {
    jd_text: string;
    skills_text: string;
    company?: string;
    role?: string;
    model_id?: string;
  }): Observable<MatchCheckResult> {
    return this.http.post<MatchCheckResult>(`${this.baseUrl}/check-match`, {
      ...payload,
      model_id: payload.model_id || this.selectedModel(),
    });
  }

  uploadResumeAndCheckMatch(
    file: File,
    jdText: string,
    company: string = '',
    role: string = '',
    modelId: string = 'auto'
  ): Observable<MatchCheckResult> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('jd_text', jdText);
    formData.append('company', company);
    formData.append('role', role);
    formData.append('model_id', modelId || this.selectedModel());

    return this.http.post<MatchCheckResult>(`${this.baseUrl}/upload-resume-for-match`, formData);
  }

  getCareerSites(): Observable<CareerSite[]> {
    return this.http.get<CareerSite[]>(`${this.baseUrl}/career-sites`).pipe(
      tap((sites) => this.careerSites.set(sites))
    );
  }

  addCareerSite(companyName: string, siteType: string = 'greenhouse', identifier: string = ''): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/career-sites`, {
      company_name: companyName,
      site_type: siteType,
      identifier: identifier || companyName,
    }).pipe(
      tap((res) => {
        if (res.all_sites) {
          this.careerSites.set(res.all_sites);
        }
      })
    );
  }

  getInterviewPrep(payload: {
    company: string;
    role?: string;
    jd_text?: string;
    model_id?: string;
    use_ai?: boolean;
  }): Observable<InterviewPrepResult> {
    return this.http.post<InterviewPrepResult>(`${this.baseUrl}/interview-prep`, {
      ...payload,
      model_id: payload.model_id || this.selectedModel(),
      use_ai: payload.use_ai || false,
    });
  }

  discoverJobs(
    query: string = 'Software Engineer',
    location: string = 'Remote',
    sourceFilter: string = 'all',
    page: number = 1,
    limit: number = 30,
    offset: number = 0
  ): Observable<DiscoveredJob[]> {
    return this.http.get<DiscoveredJob[]>(`${this.baseUrl}/discover-jobs`, {
      params: { query, location, source_filter: sourceFilter, page, limit, offset },
    });
  }

  exportDiscoveredJobsExcel(
    query: string = 'Software Engineer',
    location: string = 'Remote',
    sourceFilter: string = 'all',
    limit: number = 100
  ): Observable<Blob> {
    return this.http.get(`${this.baseUrl}/discover-jobs/export/excel`, {
      params: { query, location, source_filter: sourceFilter, limit },
      responseType: 'blob',
    });
  }

  trackDiscoveredJob(job: DiscoveredJob): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/track-discovered-job`, {
      company: job.company,
      role: job.role,
      location: job.location,
      salary_range: job.salary_range,
      job_url: job.job_url,
      jd_snapshot: job.jd_snapshot,
      tags: job.tags,
      relevance_score: job.relevance_score,
    });
  }

  updateKeys(payload: {
    gemini_api_key?: string;
    openai_api_key?: string;
    anthropic_api_key?: string;
    github_token?: string;
  }): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/settings/keys`, payload);
  }

  testConnection(model_id: string): Observable<{ status: string; model_id: string; message: string; latency_ms: number }> {
    return this.http.post<{ status: string; model_id: string; message: string; latency_ms: number }>(
      `${this.baseUrl}/test-connection`,
      { model_id }
    );
  }
}
