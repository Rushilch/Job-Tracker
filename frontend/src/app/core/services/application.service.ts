import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import {
  Application,
  ApplicationCreate,
  ApplicationStats,
  ApplicationStatus,
  ApplicationUpdate,
  TimelineEntry,
} from '../models/application.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ApplicationService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiBaseUrl}/applications`;

  // Signals for state management
  applications = signal<Application[]>([]);
  stats = signal<ApplicationStats | null>(null);
  isLoading = signal<boolean>(false);
  selectedApplication = signal<Application | null>(null);

  /** Load all applications */
  loadApplications(statusFilter?: ApplicationStatus, search?: string): Observable<Application[]> {
    this.isLoading.set(true);
    let params = new HttpParams();
    if (statusFilter) {
      params = params.set('status', statusFilter);
    }
    if (search) {
      params = params.set('search', search);
    }

    return this.http.get<Application[]>(this.baseUrl, { params }).pipe(
      tap({
        next: (apps) => {
          this.applications.set(apps);
          this.isLoading.set(false);
          this.loadStats().subscribe();
        },
        error: () => this.isLoading.set(false),
      })
    );
  }

  /** Load dashboard statistics */
  loadStats(): Observable<ApplicationStats> {
    return this.http.get<ApplicationStats>(`${this.baseUrl}/stats`).pipe(
      tap((stats) => this.stats.set(stats))
    );
  }

  /** Get single application by ID */
  getApplication(id: string): Observable<Application> {
    return this.http.get<Application>(`${this.baseUrl}/${id}`).pipe(
      tap((app) => this.selectedApplication.set(app))
    );
  }

  /** Create new application */
  createApplication(payload: ApplicationCreate): Observable<Application> {
    return this.http.post<Application>(this.baseUrl, payload).pipe(
      tap((newApp) => {
        this.applications.update((apps) => [newApp, ...apps]);
        this.loadStats().subscribe();
      })
    );
  }

  /** Update application */
  updateApplication(id: string, payload: ApplicationUpdate): Observable<Application> {
    return this.http.put<Application>(`${this.baseUrl}/${id}`, payload).pipe(
      tap((updated) => {
        this.applications.update((apps) =>
          apps.map((a) => (a.id === id ? updated : a))
        );
        this.loadStats().subscribe();
      })
    );
  }

  /** Update status (used in Drag & Drop) */
  updateStatus(id: string, newStatus: ApplicationStatus, note?: string): Observable<Application> {
    return this.http
      .patch<Application>(`${this.baseUrl}/${id}/status`, {
        status: newStatus,
        note,
      })
      .pipe(
        tap((updated) => {
          this.applications.update((apps) =>
            apps.map((a) => (a.id === id ? updated : a))
          );
          this.loadStats().subscribe();
        })
      );
  }

  /** Add timeline note */
  addTimelineEntry(id: string, entry: TimelineEntry): Observable<Application> {
    return this.http.post<Application>(`${this.baseUrl}/${id}/timeline`, entry).pipe(
      tap((updated) => {
        this.applications.update((apps) =>
          apps.map((a) => (a.id === id ? updated : a))
        );
      })
    );
  }

  /** Upload resume file for an application */
  uploadResume(id: string, file: File): Observable<Application> {
    const formData = new FormData();
    formData.append('file', file, file.name);

    return this.http.post<Application>(`${this.baseUrl}/${id}/resume/upload`, formData).pipe(
      tap((updated) => {
        this.applications.update((apps) =>
          apps.map((a) => (a.id === id ? updated : a))
        );
        if (this.selectedApplication()?.id === id) {
          this.selectedApplication.set(updated);
        }
      })
    );
  }

  /** Run AI Resume Tailoring via Agent Service */
  tailorApplicationResume(id: string): Observable<any> {
    return this.http.post<any>(`${environment.apiBaseUrl}/agent/tailor-application/${id}`, {}).pipe(
      tap(() => {
        // Refresh application details to reflect tailored results
        this.getApplication(id).subscribe();
        this.loadApplications().subscribe();
      })
    );
  }

  /** Scrape clean JD snapshot from job URL */
  scrapeJobUrl(url: string): Observable<{ title?: string; company?: string; jd_text?: string; status: string; message: string }> {
    return this.http.post<any>(`${environment.apiBaseUrl}/agent/scrape-job`, { url });
  }

  /** Trigger download of Excel report */
  exportExcel(): void {
    const downloadUrl = `${this.baseUrl}/export/excel`;
    window.open(downloadUrl, '_blank');
  }

  /** Delete application */
  deleteApplication(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`).pipe(
      tap(() => {
        this.applications.update((apps) => apps.filter((a) => a.id !== id));
        this.loadStats().subscribe();
      })
    );
  }
}
