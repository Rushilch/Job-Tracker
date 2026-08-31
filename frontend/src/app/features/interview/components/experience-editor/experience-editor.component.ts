import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../../../core/services/interview-lab.service';
import {
  Experience,
  ExperienceCreate,
  InterviewProcessStep,
  InterviewQA,
  ResourceLink,
} from '../../../../core/models/interview-lab.model';

@Component({
  selector: 'app-experience-editor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './experience-editor.component.html',
  styleUrls: ['./experience-editor.component.scss'],
})
export class ExperienceEditorComponent implements OnInit {
  labService = inject(InterviewLabService);

  @Input() experienceToEdit: Experience | null = null;
  @Input() defaultApplicationId: string | null = null;
  @Input() defaultCompany: string | null = null;
  @Input() defaultRole: string | null = null;
  @Output() saved = new EventEmitter<Experience>();
  @Output() cancelled = new EventEmitter<void>();

  applicationId = signal<string | null>(null);
  company = signal<string>('');
  role = signal<string>('Software Engineer');
  interviewDate = signal<string>('');
  outcome = signal<string>('Pending');
  rating = signal<number>(7);
  overallNotes = signal<string>('');
  selectedTags = signal<string[]>([]);

  // Pipeline process steps
  processSteps = signal<InterviewProcessStep[]>([]);

  // Questions asked in loop
  questionsAsked = signal<InterviewQA[]>([]);

  // Resource Links
  links = signal<ResourceLink[]>([]);
  newLinkLabel = signal<string>('');
  newLinkUrl = signal<string>('');

  isSaving = signal<boolean>(false);
  errorMessage = signal<string>('');

  roundTypes = [
    { label: 'OA (Online Assessment)', value: 'OA' },
    { label: 'TA (Technical / Coding)', value: 'TA' },
    { label: 'SD (System Design)', value: 'SD' },
    { label: 'BA (Behavioral / Values)', value: 'BA' },
    { label: 'HM (Hiring Manager)', value: 'HM' },
    { label: 'HR (Recruiter Screen)', value: 'HR' },
    { label: 'Presentation / Takehome', value: 'Takehome' },
  ];

  outcomes = ['Pending', 'Offer Received 🎉', 'Rejected', 'Withdrawn', 'Ghosted'];

  categories = ['Technical', 'Behavioral', 'System Design', 'Other'];

  ngOnInit(): void {
    if (this.experienceToEdit) {
      this.applicationId.set(this.experienceToEdit.application_id || this.defaultApplicationId);
      this.company.set(this.experienceToEdit.company || this.defaultCompany || '');
      this.role.set(this.experienceToEdit.role || this.defaultRole || 'Software Engineer');
      this.interviewDate.set(
        this.experienceToEdit.date ? this.experienceToEdit.date.slice(0, 10) : ''
      );
      this.outcome.set(this.experienceToEdit.outcome || 'Pending');
      this.rating.set(this.experienceToEdit.rating || 7);
      this.overallNotes.set(this.experienceToEdit.overall_notes || '');
      this.selectedTags.set([...this.experienceToEdit.tags]);
      this.processSteps.set(
        this.experienceToEdit.interview_process.length > 0
          ? JSON.parse(JSON.stringify(this.experienceToEdit.interview_process))
          : this.getDefaultProcess()
      );
      this.questionsAsked.set(
        this.experienceToEdit.questions_asked.length > 0
          ? JSON.parse(JSON.stringify(this.experienceToEdit.questions_asked))
          : [this.createEmptyQA()]
      );
      this.links.set(JSON.parse(JSON.stringify(this.experienceToEdit.links || [])));
    } else {
      this.applicationId.set(this.defaultApplicationId);
      this.company.set(this.defaultCompany || '');
      this.role.set(this.defaultRole || 'Software Engineer');
      this.processSteps.set(this.getDefaultProcess());
      this.questionsAsked.set([this.createEmptyQA()]);
      this.interviewDate.set(new Date().toISOString().slice(0, 10));
    }
  }

  private getDefaultProcess(): InterviewProcessStep[] {
    return [
      { round_number: 1, round_type: 'OA', description: '70 min HackerRank coding challenge' },
      { round_number: 2, round_type: 'TA', description: '45 min technical phone screen' },
      { round_number: 3, round_type: 'TA', description: 'Virtual onsite coding round 1' },
      { round_number: 4, round_type: 'SD', description: 'System design architecture round' },
      { round_number: 5, round_type: 'BA', description: 'Behavioral & leadership principles' },
    ];
  }

  private createEmptyQA(): InterviewQA {
    return {
      question: '',
      answer: '',
      category: 'Technical',
      links: [],
    };
  }

  // --- Process Pipeline Actions ---
  addProcessStep() {
    const list = [...this.processSteps()];
    list.push({
      round_number: list.length + 1,
      round_type: 'TA',
      description: '',
    });
    this.processSteps.set(list);
  }

  removeProcessStep(index: number) {
    const list = [...this.processSteps()];
    list.splice(index, 1);
    // re-number rounds
    list.forEach((step, idx) => (step.round_number = idx + 1));
    this.processSteps.set(list);
  }

  // --- Questions Asked Actions ---
  addQuestionQA() {
    const list = [...this.questionsAsked()];
    list.push(this.createEmptyQA());
    this.questionsAsked.set(list);
  }

  removeQuestionQA(index: number) {
    const list = [...this.questionsAsked()];
    if (list.length <= 1) {
      alert('At least one question is required.');
      return;
    }
    list.splice(index, 1);
    this.questionsAsked.set(list);
  }

  // --- Links Actions ---
  addLink() {
    const label = this.newLinkLabel().trim();
    const url = this.newLinkUrl().trim();
    if (!url) return;

    const list = [...this.links()];
    list.push({ label: label || url, url });
    this.links.set(list);
    this.newLinkLabel.set('');
    this.newLinkUrl.set('');
  }

  removeLink(index: number) {
    const list = [...this.links()];
    list.splice(index, 1);
    this.links.set(list);
  }

  toggleTag(tagName: string) {
    const current = [...this.selectedTags()];
    const idx = current.indexOf(tagName);
    if (idx > -1) {
      current.splice(idx, 1);
    } else {
      current.push(tagName);
    }
    this.selectedTags.set(current);
  }

  onSave() {
    if (!this.company().trim()) {
      this.errorMessage.set('Company name is required.');
      return;
    }

    this.isSaving.set(true);
    this.errorMessage.set('');

    const payload: ExperienceCreate = {
      company: this.company().trim(),
      role: this.role().trim() || 'Software Engineer',
      application_id: this.applicationId(),
      date: this.interviewDate() ? new Date(this.interviewDate()).toISOString() : null,
      interview_process: this.processSteps(),
      questions_asked: this.questionsAsked().filter((q) => q.question.trim().length > 0),
      rating: this.rating(),
      overall_notes: this.overallNotes().trim(),
      links: this.links(),
      tags: this.selectedTags(),
      outcome: this.outcome(),
    };

    if (this.experienceToEdit) {
      this.labService.updateExperience(this.experienceToEdit.id, payload).subscribe({
        next: (updated) => {
          this.isSaving.set(false);
          this.saved.emit(updated);
        },
        error: (err) => {
          this.isSaving.set(false);
          this.errorMessage.set(err?.error?.detail || err?.message || 'Failed to update experience');
        },
      });
    } else {
      this.labService.createExperience(payload).subscribe({
        next: (created) => {
          this.isSaving.set(false);
          this.saved.emit(created);
        },
        error: (err) => {
          this.isSaving.set(false);
          this.errorMessage.set(err?.error?.detail || err?.message || 'Failed to create experience');
        },
      });
    }
  }

  cancel() {
    this.cancelled.emit();
  }
}
