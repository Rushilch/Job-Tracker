import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../../../core/services/interview-lab.service';
import {
  Question,
  QuestionCreate,
  ResourceLink,
  SolutionEntry,
  Tag,
} from '../../../../core/models/interview-lab.model';

@Component({
  selector: 'app-question-editor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './question-editor.component.html',
  styleUrls: ['./question-editor.component.scss'],
})
export class QuestionEditorComponent implements OnInit {
  labService = inject(InterviewLabService);

  @Input() questionToEdit: Question | null = null;
  @Input() defaultApplicationId: string | null = null;
  @Input() defaultCompany: string | null = null;
  @Input() defaultRole: string | null = null;
  @Output() saved = new EventEmitter<Question>();
  @Output() cancelled = new EventEmitter<void>();

  title = signal<string>('');
  description = signal<string>('');
  difficulty = signal<'Easy' | 'Medium' | 'Hard'>('Medium');
  topic = signal<string>('Arrays & Hashing');
  applicationId = signal<string | null>(null);
  company = signal<string | null>(null);
  role = signal<string | null>(null);
  notes = signal<string>('');
  selectedTags = signal<string[]>([]);
  solutions = signal<SolutionEntry[]>([]);
  links = signal<ResourceLink[]>([]);

  // Active solution tab index
  activeSolutionIndex = signal<number>(0);

  // Temporary new link inputs
  newLinkLabel = signal<string>('');
  newLinkUrl = signal<string>('');

  isSaving = signal<boolean>(false);
  errorMessage = signal<string>('');

  languages = [
    { label: 'Python', value: 'python' },
    { label: 'C++', value: 'cpp' },
    { label: 'Java', value: 'java' },
    { label: 'TypeScript', value: 'typescript' },
    { label: 'JavaScript', value: 'javascript' },
    { label: 'Go', value: 'go' },
    { label: 'Rust', value: 'rust' },
    { label: 'SQL', value: 'sql' },
  ];

  popularTopics = [
    'Arrays & Hashing',
    'Two Pointers',
    'Sliding Window',
    'Stack',
    'Binary Search',
    'Linked List',
    'Trees',
    'Tries',
    'Heap / Priority Queue',
    'Backtracking',
    'Graphs',
    'Dynamic Programming',
    'Greedy',
    'Intervals',
    'Math & Geometry',
    'Bit Manipulation',
    'System / Concurrency',
  ];

  ngOnInit(): void {
    if (this.questionToEdit) {
      this.title.set(this.questionToEdit.title);
      this.description.set(this.questionToEdit.description || '');
      this.difficulty.set(this.questionToEdit.difficulty);
      this.topic.set(this.questionToEdit.topic || 'Arrays & Hashing');
      this.applicationId.set(this.questionToEdit.application_id || this.defaultApplicationId);
      this.company.set(this.questionToEdit.company || this.defaultCompany);
      this.role.set(this.questionToEdit.role || this.defaultRole);
      this.notes.set(this.questionToEdit.notes || '');
      this.selectedTags.set([...this.questionToEdit.tags]);
      this.solutions.set(
        this.questionToEdit.solutions.length > 0
          ? JSON.parse(JSON.stringify(this.questionToEdit.solutions))
          : [this.createEmptySolution(1)]
      );
      this.links.set(JSON.parse(JSON.stringify(this.questionToEdit.links || [])));
    } else {
      // New question with 1 default solution
      this.applicationId.set(this.defaultApplicationId);
      this.company.set(this.defaultCompany);
      this.role.set(this.defaultRole);
      this.solutions.set([this.createEmptySolution(1)]);
    }
  }

  private createEmptySolution(index: number): SolutionEntry {
    return {
      label: `Solution ${index}`,
      code: '',
      language: 'python',
      explanation: '',
      time_complexity: '',
      space_complexity: '',
      tags: [],
    };
  }

  addSolution() {
    const list = [...this.solutions()];
    list.push(this.createEmptySolution(list.length + 1));
    this.solutions.set(list);
    this.activeSolutionIndex.set(list.length - 1);
  }

  removeSolution(index: number, event: MouseEvent) {
    event.stopPropagation();
    const list = [...this.solutions()];
    if (list.length <= 1) {
      alert('At least one solution entry is required.');
      return;
    }
    list.splice(index, 1);
    this.solutions.set(list);
    if (this.activeSolutionIndex() >= list.length) {
      this.activeSolutionIndex.set(Math.max(0, list.length - 1));
    }
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

  onSave() {
    if (!this.title().trim()) {
      this.errorMessage.set('Question title is required.');
      return;
    }

    this.isSaving.set(true);
    this.errorMessage.set('');

    const payload: QuestionCreate = {
      title: this.title().trim(),
      description: this.description().trim(),
      difficulty: this.difficulty(),
      topic: this.topic().trim(),
      application_id: this.applicationId(),
      company: this.company(),
      role: this.role(),
      solutions: this.solutions(),
      links: this.links(),
      tags: this.selectedTags(),
      notes: this.notes().trim(),
    };

    if (this.questionToEdit) {
      this.labService.updateQuestion(this.questionToEdit.id, payload).subscribe({
        next: (updated) => {
          this.isSaving.set(false);
          this.saved.emit(updated);
        },
        error: (err) => {
          this.isSaving.set(false);
          this.errorMessage.set(err?.error?.detail || err?.message || 'Failed to update question');
        },
      });
    } else {
      this.labService.createQuestion(payload).subscribe({
        next: (created) => {
          this.isSaving.set(false);
          this.saved.emit(created);
        },
        error: (err) => {
          this.isSaving.set(false);
          this.errorMessage.set(err?.error?.detail || err?.message || 'Failed to create question');
        },
      });
    }
  }

  cancel() {
    this.cancelled.emit();
  }
}
