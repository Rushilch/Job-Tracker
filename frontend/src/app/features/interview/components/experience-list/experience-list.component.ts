import { Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../../../core/services/interview-lab.service';
import { Experience } from '../../../../core/models/interview-lab.model';

@Component({
  selector: 'app-experience-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './experience-list.component.html',
  styleUrls: ['./experience-list.component.scss'],
})
export class ExperienceListComponent {
  labService = inject(InterviewLabService);

  @Input() selectedApplicationId: string | null = null;
  @Input() selectedCompany: string | null = null;
  @Output() addExperience = new EventEmitter<void>();
  @Output() editExperience = new EventEmitter<Experience>();

  searchCompany = signal<string>('');
  selectedTag = signal<string>('All');
  selectedMinRating = signal<number>(0);

  expandedExperiences = signal<Set<string>>(new Set());

  onFilterChange() {
    this.labService.loadExperiences({
      applicationId: this.selectedApplicationId,
      company: this.searchCompany() || this.selectedCompany,
      tag: this.selectedTag(),
      minRating: this.selectedMinRating() > 0 ? this.selectedMinRating() : undefined,
    }).subscribe();
  }

  toggleExpand(id: string) {
    const next = new Set(this.expandedExperiences());
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    this.expandedExperiences.set(next);
  }

  onDelete(exp: Experience, event: MouseEvent) {
    event.stopPropagation();
    if (confirm(`Delete interview experience for "${exp.company}"?`)) {
      this.labService.deleteExperience(exp.id).subscribe();
    }
  }

  getTagColor(tagName: string): string {
    const found = this.labService.tags().find((t) => t.name.toLowerCase() === tagName.toLowerCase());
    return found ? found.color : '#c25e2e';
  }

  formatDate(dateStr?: string | null): string {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  }

  getOutcomeClass(outcome?: string): string {
    if (!outcome) return 'outcome-pending';
    const lower = outcome.toLowerCase();
    if (lower.includes('offer')) return 'outcome-offer';
    if (lower.includes('reject')) return 'outcome-rejected';
    if (lower.includes('ghost')) return 'outcome-ghosted';
    return 'outcome-pending';
  }
}
