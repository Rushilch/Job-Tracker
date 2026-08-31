import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AgentService, MatchCheckResult } from '../../core/services/agent.service';
import { ApplicationService } from '../../core/services/application.service';

@Component({
  selector: 'app-match-checker',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './match-checker.component.html',
  styleUrls: ['./match-checker.component.scss'],
})
export class MatchCheckerComponent implements OnInit {
  company = signal<string>('Google');
  role = signal<string>('Software Engineer - Cloud Backend');
  inputMode = signal<'upload' | 'paste'>('upload');
  selectedFile = signal<File | null>(null);
  fileName = signal<string>('');
  skillsText = signal<string>('Python, FastAPI, Docker, Asyncio, MongoDB, PostgreSQL, Angular, TypeScript, Git, CI/CD, Distributed Systems');
  jdText = signal<string>(`About the job:
We are looking for a Software Engineer to design and scale high-throughput cloud services.
Requirements:
- 2+ years experience building asynchronous backend APIs with Python and FastAPI or Go.
- Strong proficiency in Docker containerization, REST API architecture, and microservices.
- Experience with relational and NoSQL databases (PostgreSQL, MongoDB).
- Familiarity with Angular, Redis caching, and CI/CD pipelines is a plus.`);

  isLoading = signal<boolean>(false);
  isSaving = signal<boolean>(false);
  result = signal<MatchCheckResult | null>(null);
  saveSuccess = signal<boolean>(false);
  copiedIndex = signal<number | null>(null);

  constructor(
    public agentService: AgentService,
    private applicationService: ApplicationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.agentService.loadModels().subscribe();
  }

  onFileSelected(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      this.selectedFile.set(file);
      this.fileName.set(file.name);
    }
  }

  onCopyBullet(text: string, index: number) {
    navigator.clipboard.writeText(text);
    this.copiedIndex.set(index);
    setTimeout(() => this.copiedIndex.set(null), 2000);
  }

  onRunAnalysis() {
    if (!this.jdText()) {
      alert('Please provide the Job Description text.');
      return;
    }

    if (this.inputMode() === 'upload' && !this.selectedFile()) {
      alert('Please upload a resume file (PDF, TXT) or switch to Paste mode.');
      return;
    }

    if (this.inputMode() === 'paste' && !this.skillsText()) {
      alert('Please paste your resume or skills text.');
      return;
    }

    this.isLoading.set(true);
    this.saveSuccess.set(false);

    if (this.inputMode() === 'upload' && this.selectedFile()) {
      this.agentService.uploadResumeAndCheckMatch(
        this.selectedFile()!,
        this.jdText(),
        this.company(),
        this.role(),
        this.agentService.selectedModel()
      ).subscribe({
        next: (res) => {
          this.isLoading.set(false);
          this.result.set(res);
        },
        error: (err) => {
          this.isLoading.set(false);
          alert('ATS Resume Scan failed: ' + (err.error?.detail || err.message));
        },
      });
    } else {
      this.agentService.checkMatch({
        company: this.company(),
        role: this.role(),
        jd_text: this.jdText(),
        skills_text: this.skillsText(),
        model_id: this.agentService.selectedModel(),
      }).subscribe({
        next: (res) => {
          this.isLoading.set(false);
          this.result.set(res);
        },
        error: (err) => {
          this.isLoading.set(false);
          alert('Match analysis failed: ' + (err.error?.detail || err.message));
        },
      });
    }
  }

  onSaveToTracker() {
    const res = this.result();
    if (!res) return;

    this.isSaving.set(true);
    this.applicationService.createApplication({
      company: this.company(),
      role: this.role(),
      location: 'Remote',
      jd_snapshot: this.jdText(),
      status: 'discovered',
      tags: ['ATS Scanned', res.ats_rating || res.verdict],
      relevance_score: res.ats_score || res.match_percentage,
    }).subscribe({
      next: () => {
        this.isSaving.set(false);
        this.saveSuccess.set(true);
        setTimeout(() => this.router.navigate(['/kanban']), 1200);
      },
      error: () => {
        this.isSaving.set(false);
        alert('Failed to save to application tracker.');
      },
    });
  }
}
