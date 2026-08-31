import { Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../../../core/services/interview-lab.service';
import { Question } from '../../../../core/models/interview-lab.model';

@Component({
  selector: 'app-question-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './question-list.component.html',
  styleUrls: ['./question-list.component.scss'],
})
export class QuestionListComponent {
  labService = inject(InterviewLabService);

  @Input() selectedApplicationId: string | null = null;
  @Input() selectedCompany: string | null = null;
  @Output() addQuestion = new EventEmitter<void>();
  @Output() editQuestion = new EventEmitter<Question>();

  // Filter states
  selectedDifficulty = signal<string>('All');
  selectedTag = signal<string>('All');
  searchQuery = signal<string>('');

  // Track expanded solutions & active solution tabs per question ID
  expandedQuestions = signal<Set<string>>(new Set());
  activeSolutionMap = signal<Record<string, number>>({});
  copiedCodeId = signal<string | null>(null);

  difficulties = ['All', 'Easy', 'Medium', 'Hard'];

  onFilterChange() {
    this.labService.loadQuestions({
      applicationId: this.selectedApplicationId,
      company: this.selectedCompany,
      difficulty: this.selectedDifficulty(),
      tag: this.selectedTag(),
      search: this.searchQuery(),
    }).subscribe();
  }

  toggleExpand(questionId: string) {
    const next = new Set(this.expandedQuestions());
    if (next.has(questionId)) {
      next.delete(questionId);
    } else {
      next.add(questionId);
    }
    this.expandedQuestions.set(next);
  }

  setActiveSolution(questionId: string, solIndex: number) {
    const current = { ...this.activeSolutionMap() };
    current[questionId] = solIndex;
    this.activeSolutionMap.set(current);
  }

  getActiveSolutionIndex(questionId: string): number {
    return this.activeSolutionMap()[questionId] || 0;
  }

  copyCode(code: string, id: string) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(code).then(() => {
        this.copiedCodeId.set(id);
        setTimeout(() => this.copiedCodeId.set(null), 2000);
      });
    }
  }

  onDelete(question: Question, event: MouseEvent) {
    event.stopPropagation();
    if (confirm(`Are you sure you want to delete question "${question.title}"?`)) {
      this.labService.deleteQuestion(question.id).subscribe();
    }
  }

  getTagColor(tagName: string): string {
    const found = this.labService.tags().find((t) => t.name.toLowerCase() === tagName.toLowerCase());
    return found ? found.color : '#c25e2e';
  }
}
