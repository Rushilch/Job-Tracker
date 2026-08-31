import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import {
  Experience,
  ExperienceCreate,
  ExperienceUpdate,
  FlashCard,
  FlashCardCreate,
  FlashCardUpdate,
  Question,
  QuestionCreate,
  QuestionUpdate,
  Tag,
  TagCreate,
} from '../models/interview-lab.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class InterviewLabService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiBaseUrl}/interview-lab`;

  // Signals for state management
  tags = signal<Tag[]>([]);
  questions = signal<Question[]>([]);
  experiences = signal<Experience[]>([]);
  flashcards = signal<FlashCard[]>([]);

  isLoading = signal<boolean>(false);
  errorMessage = signal<string>('');

  // -------------------------------------------------------------------------
  // Tags API
  // -------------------------------------------------------------------------
  loadTags(): Observable<Tag[]> {
    return this.http.get<Tag[]>(`${this.baseUrl}/tags`).pipe(
      tap((tags) => this.tags.set(tags))
    );
  }

  createTag(payload: TagCreate): Observable<Tag> {
    return this.http.post<Tag>(`${this.baseUrl}/tags`, payload).pipe(
      tap((newTag) => {
        this.tags.update((tags) => {
          const exists = tags.some((t) => t.id === newTag.id || t.name.toLowerCase() === newTag.name.toLowerCase());
          return exists ? tags : [newTag, ...tags];
        });
      })
    );
  }

  deleteTag(tagId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/tags/${tagId}`).pipe(
      tap(() => {
        this.tags.update((tags) => tags.filter((t) => t.id !== tagId));
      })
    );
  }

  // -------------------------------------------------------------------------
  // Questions API
  // -------------------------------------------------------------------------
  loadQuestions(filter?: {
    applicationId?: string | null;
    company?: string | null;
    difficulty?: string;
    tag?: string;
    search?: string;
  }): Observable<Question[]> {
    this.isLoading.set(true);
    let params = new HttpParams();
    if (filter?.applicationId) {
      params = params.set('application_id', filter.applicationId);
    } else if (filter?.company) {
      params = params.set('company', filter.company);
    }
    if (filter?.difficulty && filter.difficulty !== 'All') {
      params = params.set('difficulty', filter.difficulty);
    }
    if (filter?.tag && filter.tag !== 'All') {
      params = params.set('tag', filter.tag);
    }
    if (filter?.search) {
      params = params.set('search', filter.search);
    }

    return this.http.get<Question[]>(`${this.baseUrl}/questions`, { params }).pipe(
      tap({
        next: (questions) => {
          this.questions.set(questions);
          this.isLoading.set(false);
        },
        error: (err) => {
          this.isLoading.set(false);
          this.errorMessage.set(err?.message || 'Failed to load questions');
        },
      })
    );
  }

  getQuestion(id: string): Observable<Question> {
    return this.http.get<Question>(`${this.baseUrl}/questions/${id}`);
  }

  createQuestion(payload: QuestionCreate): Observable<Question> {
    return this.http.post<Question>(`${this.baseUrl}/questions`, payload).pipe(
      tap((newQ) => {
        this.questions.update((list) => [newQ, ...list]);
      })
    );
  }

  updateQuestion(id: string, payload: QuestionUpdate): Observable<Question> {
    return this.http.put<Question>(`${this.baseUrl}/questions/${id}`, payload).pipe(
      tap((updated) => {
        this.questions.update((list) => list.map((q) => (q.id === id ? updated : q)));
      })
    );
  }

  deleteQuestion(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/questions/${id}`).pipe(
      tap(() => {
        this.questions.update((list) => list.filter((q) => q.id !== id));
      })
    );
  }

  // -------------------------------------------------------------------------
  // Experiences API
  // -------------------------------------------------------------------------
  loadExperiences(filter?: {
    applicationId?: string | null;
    company?: string | null;
    tag?: string;
    minRating?: number;
  }): Observable<Experience[]> {
    this.isLoading.set(true);
    let params = new HttpParams();
    if (filter?.applicationId) {
      params = params.set('application_id', filter.applicationId);
    } else if (filter?.company) {
      params = params.set('company', filter.company);
    }
    if (filter?.tag && filter.tag !== 'All') {
      params = params.set('tag', filter.tag);
    }
    if (filter?.minRating) {
      params = params.set('min_rating', filter.minRating.toString());
    }

    return this.http.get<Experience[]>(`${this.baseUrl}/experiences`, { params }).pipe(
      tap({
        next: (exps) => {
          this.experiences.set(exps);
          this.isLoading.set(false);
        },
        error: (err) => {
          this.isLoading.set(false);
          this.errorMessage.set(err?.message || 'Failed to load interview experiences');
        },
      })
    );
  }

  getExperience(id: string): Observable<Experience> {
    return this.http.get<Experience>(`${this.baseUrl}/experiences/${id}`);
  }

  createExperience(payload: ExperienceCreate): Observable<Experience> {
    return this.http.post<Experience>(`${this.baseUrl}/experiences`, payload).pipe(
      tap((newExp) => {
        this.experiences.update((list) => [newExp, ...list]);
      })
    );
  }

  updateExperience(id: string, payload: ExperienceUpdate): Observable<Experience> {
    return this.http.put<Experience>(`${this.baseUrl}/experiences/${id}`, payload).pipe(
      tap((updated) => {
        this.experiences.update((list) => list.map((e) => (e.id === id ? updated : e)));
      })
    );
  }

  deleteExperience(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/experiences/${id}`).pipe(
      tap(() => {
        this.experiences.update((list) => list.filter((e) => e.id !== id));
      })
    );
  }

  // -------------------------------------------------------------------------
  // Flash Cards API
  // -------------------------------------------------------------------------
  loadFlashcards(filter?: {
    applicationId?: string | null;
    company?: string | null;
    tag?: string;
    difficulty?: string;
  }): Observable<FlashCard[]> {
    this.isLoading.set(true);
    let params = new HttpParams();
    if (filter?.applicationId) {
      params = params.set('application_id', filter.applicationId);
    } else if (filter?.company) {
      params = params.set('company', filter.company);
    }
    if (filter?.tag && filter.tag !== 'All') {
      params = params.set('tag', filter.tag);
    }
    if (filter?.difficulty && filter.difficulty !== 'All') {
      params = params.set('difficulty', filter.difficulty);
    }

    return this.http.get<FlashCard[]>(`${this.baseUrl}/flashcards`, { params }).pipe(
      tap({
        next: (cards) => {
          this.flashcards.set(cards);
          this.isLoading.set(false);
        },
        error: (err) => {
          this.isLoading.set(false);
          this.errorMessage.set(err?.message || 'Failed to load flashcards');
        },
      })
    );
  }

  getStudyDeck(options?: {
    applicationId?: string | null;
    company?: string | null;
    count?: number;
    tag?: string;
    difficulty?: string;
    shuffle?: boolean;
  }): Observable<FlashCard[]> {
    let params = new HttpParams();
    if (options?.applicationId) params = params.set('application_id', options.applicationId);
    else if (options?.company) params = params.set('company', options.company);
    if (options?.count) params = params.set('count', options.count.toString());
    if (options?.tag && options.tag !== 'All') params = params.set('tag', options.tag);
    if (options?.difficulty && options.difficulty !== 'All') params = params.set('difficulty', options.difficulty);
    if (options?.shuffle !== undefined) params = params.set('shuffle', options.shuffle.toString());

    return this.http.get<FlashCard[]>(`${this.baseUrl}/flashcards/study`, { params });
  }

  createFlashcard(payload: FlashCardCreate): Observable<FlashCard> {
    return this.http.post<FlashCard>(`${this.baseUrl}/flashcards`, payload).pipe(
      tap((newCard) => {
        this.flashcards.update((list) => [newCard, ...list]);
      })
    );
  }

  updateFlashcard(id: string, payload: FlashCardUpdate): Observable<FlashCard> {
    return this.http.put<FlashCard>(`${this.baseUrl}/flashcards/${id}`, payload).pipe(
      tap((updated) => {
        this.flashcards.update((list) => list.map((c) => (c.id === id ? updated : c)));
      })
    );
  }

  deleteFlashcard(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/flashcards/${id}`).pipe(
      tap(() => {
        this.flashcards.update((list) => list.filter((c) => c.id !== id));
      })
    );
  }

  // -------------------------------------------------------------------------
  // Excel Export
  // -------------------------------------------------------------------------
  exportExcel(applicationId?: string | null, company?: string | null): void {
    let queryParams = [];
    if (applicationId) queryParams.push(`application_id=${encodeURIComponent(applicationId)}`);
    if (company) queryParams.push(`company=${encodeURIComponent(company)}`);
    const qs = queryParams.length > 0 ? `?${queryParams.join('&')}` : '';
    const downloadUrl = `${this.baseUrl}/export/excel${qs}`;
    window.open(downloadUrl, '_blank');
  }
}
