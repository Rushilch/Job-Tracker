import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AgentService } from './core/services/agent.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent implements OnInit {
  title = 'CareerPilot';

  // Dark Mode State
  isDarkMode = signal<boolean>(false);

  // API Keys Modal State
  showSettingsModal = signal<boolean>(false);
  geminiKey = signal<string>('');
  openaiKey = signal<string>('');
  anthropicKey = signal<string>('');
  githubToken = signal<string>('');
  isSavingKeys = signal<boolean>(false);
  saveSuccessMessage = signal<string>('');

  // Diagnostic Test States
  testingModel = signal<string | null>(null);
  diagnosticResults = signal<Record<string, { status: string; message: string; latency_ms?: number }>>({});

  constructor(public agentService: AgentService) {}

  ngOnInit(): void {
    this.initTheme();
    this.agentService.loadModels().subscribe();
  }

  private initTheme() {
    const savedTheme = localStorage.getItem('careerpilot_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isDark = savedTheme === 'dark' || (!savedTheme && prefersDark);
    this.isDarkMode.set(isDark);
    this.applyTheme(isDark);
  }

  toggleDarkMode() {
    const nextState = !this.isDarkMode();
    this.isDarkMode.set(nextState);
    localStorage.setItem('careerpilot_theme', nextState ? 'dark' : 'light');
    this.applyTheme(nextState);
  }

  private applyTheme(isDark: boolean) {
    if (typeof document !== 'undefined') {
      document.body.classList.toggle('dark-theme', isDark);
      if (isDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
    }
  }

  onModelChange(newModel: string) {
    this.agentService.selectedModel.set(newModel);
  }

  openSettings() {
    this.saveSuccessMessage.set('');
    this.showSettingsModal.set(true);
  }

  closeSettings() {
    this.showSettingsModal.set(false);
  }

  onSaveKeys() {
    this.isSavingKeys.set(true);
    this.saveSuccessMessage.set('');

    this.agentService.updateKeys({
      gemini_api_key: this.geminiKey(),
      openai_api_key: this.openaiKey(),
      anthropic_api_key: this.anthropicKey(),
      github_token: this.githubToken(),
    }).subscribe({
      next: () => {
        this.isSavingKeys.set(false);
        this.saveSuccessMessage.set('API Keys saved & activated in backend successfully!');
        this.agentService.loadModels().subscribe();
      },
      error: (err) => {
        this.isSavingKeys.set(false);
        this.saveSuccessMessage.set(`Error saving keys: ${err?.message || 'Unknown'}`);
      },
    });
  }

  onTestConnection(modelId: string) {
    this.testingModel.set(modelId);
    this.agentService.testConnection(modelId).subscribe({
      next: (res) => {
        this.testingModel.set(null);
        const results = { ...this.diagnosticResults() };
        results[modelId] = {
          status: res.status,
          message: res.message,
          latency_ms: res.latency_ms,
        };
        this.diagnosticResults.set(results);
      },
      error: (err) => {
        this.testingModel.set(null);
        const results = { ...this.diagnosticResults() };
        results[modelId] = {
          status: 'error',
          message: `Connection failed: ${err?.error?.detail || err?.message || 'Server error'}`,
        };
        this.diagnosticResults.set(results);
      },
    });
  }
}
