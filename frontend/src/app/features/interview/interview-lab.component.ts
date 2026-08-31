import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService, InterviewPrepResult } from '../../core/services/agent.service';

@Component({
  selector: 'app-interview-lab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './interview-lab.component.html',
  styleUrls: ['./interview-lab.component.scss'],
})
export class InterviewLabComponent implements OnInit {
  company = signal<string>('Google');
  role = signal<string>('Software Engineer');
  jdText = signal<string>('');
  useAi = signal<boolean>(false);
  isLoading = signal<boolean>(false);
  prepDoc = signal<InterviewPrepResult | null>(null);
  expandedHints = signal<Set<number>>(new Set());

  quickCompanies = ['Google', 'Amazon', 'Meta', 'Stripe', 'Netflix', 'Bloomberg', 'Microsoft'];

  errorMessage = signal<string>('');

  constructor(public agentService: AgentService) {}

  ngOnInit(): void {
    this.agentService.loadModels().subscribe();
    this.onFetchPrep(false);
  }

  onSelectQuickCompany(comp: string) {
    this.company.set(comp);
    this.onFetchPrep(false);
  }

  toggleHint(idx: number) {
    const next = new Set(this.expandedHints());
    if (next.has(idx)) {
      next.delete(idx);
    } else {
      next.add(idx);
    }
    this.expandedHints.set(next);
  }

  onFetchPrep(forceAi: boolean = false) {
    if (!this.company()) return;

    this.isLoading.set(true);
    this.errorMessage.set('');
    this.expandedHints.set(new Set());
    this.useAi.set(forceAi);

    this.agentService.getInterviewPrep({
      company: this.company(),
      role: this.role() || 'Software Engineer',
      jd_text: this.jdText(),
      model_id: this.agentService.selectedModel(),
      use_ai: forceAi,
    }).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        this.prepDoc.set(res);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err?.error?.detail || err?.message || 'Failed to generate prep kit. Please check connection.');
      },
    });
  }
}
