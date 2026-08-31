import { Component, EventEmitter, Input, OnInit, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../../../core/services/interview-lab.service';
import { FlashCard, FlashCardCreate, ResourceLink } from '../../../../core/models/interview-lab.model';

@Component({
  selector: 'app-flashcard-editor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './flashcard-editor.component.html',
  styleUrls: ['./flashcard-editor.component.scss'],
})
export class FlashcardEditorComponent implements OnInit {
  labService = inject(InterviewLabService);

  @Input() cardToEdit: FlashCard | null = null;
  @Input() defaultApplicationId: string | null = null;
  @Input() defaultCompany: string | null = null;
  @Output() saved = new EventEmitter<FlashCard>();
  @Output() cancelled = new EventEmitter<void>();

  front = signal<string>('');
  back = signal<string>('');
  applicationId = signal<string | null>(null);
  company = signal<string | null>(null);
  difficulty = signal<'Easy' | 'Medium' | 'Hard'>('Medium');
  selectedTags = signal<string[]>([]);

  links = signal<ResourceLink[]>([]);
  newLinkLabel = signal<string>('');
  newLinkUrl = signal<string>('');

  isSaving = signal<boolean>(false);
  errorMessage = signal<string>('');

  ngOnInit(): void {
    if (this.cardToEdit) {
      this.front.set(this.cardToEdit.front);
      this.back.set(this.cardToEdit.back);
      this.applicationId.set(this.cardToEdit.application_id || this.defaultApplicationId);
      this.company.set(this.cardToEdit.company || this.defaultCompany);
      this.difficulty.set(this.cardToEdit.difficulty);
      this.selectedTags.set([...this.cardToEdit.tags]);
      this.links.set(JSON.parse(JSON.stringify(this.cardToEdit.links || [])));
    } else {
      this.applicationId.set(this.defaultApplicationId);
      this.company.set(this.defaultCompany);
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
    if (!this.front().trim() || !this.back().trim()) {
      this.errorMessage.set('Both Front (prompt) and Back (answer) are required.');
      return;
    }

    this.isSaving.set(true);
    this.errorMessage.set('');

    const payload: FlashCardCreate = {
      front: this.front().trim(),
      back: this.back().trim(),
      application_id: this.applicationId(),
      company: this.company(),
      difficulty: this.difficulty(),
      tags: this.selectedTags(),
      links: this.links(),
    };

    if (this.cardToEdit) {
      this.labService.updateFlashcard(this.cardToEdit.id, payload).subscribe({
        next: (updated) => {
          this.isSaving.set(false);
          this.saved.emit(updated);
        },
        error: (err) => {
          this.isSaving.set(false);
          this.errorMessage.set(err?.error?.detail || err?.message || 'Failed to update flashcard');
        },
      });
    } else {
      this.labService.createFlashcard(payload).subscribe({
        next: (created) => {
          this.isSaving.set(false);
          this.saved.emit(created);
        },
        error: (err) => {
          this.isSaving.set(false);
          this.errorMessage.set(err?.error?.detail || err?.message || 'Failed to create flashcard');
        },
      });
    }
  }

  cancel() {
    this.cancelled.emit();
  }
}
