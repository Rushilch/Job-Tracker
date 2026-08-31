import { Component, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../../../core/services/interview-lab.service';
import { FlashCard } from '../../../../core/models/interview-lab.model';

@Component({
  selector: 'app-flashcard-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './flashcard-list.component.html',
  styleUrls: ['./flashcard-list.component.scss'],
})
export class FlashcardListComponent {
  labService = inject(InterviewLabService);

  @Input() selectedApplicationId: string | null = null;
  @Input() selectedCompany: string | null = null;
  @Output() addCard = new EventEmitter<void>();
  @Output() editCard = new EventEmitter<FlashCard>();
  @Output() startStudy = new EventEmitter<{ tag: string; difficulty: string }>();

  selectedTag = signal<string>('All');
  selectedDifficulty = signal<string>('All');

  expandedCards = signal<Set<string>>(new Set());

  difficulties = ['All', 'Easy', 'Medium', 'Hard'];

  onFilterChange() {
    this.labService.loadFlashcards({
      applicationId: this.selectedApplicationId,
      company: this.selectedCompany,
      tag: this.selectedTag(),
      difficulty: this.selectedDifficulty(),
    }).subscribe();
  }

  toggleFlip(cardId: string) {
    const next = new Set(this.expandedCards());
    if (next.has(cardId)) {
      next.delete(cardId);
    } else {
      next.add(cardId);
    }
    this.expandedCards.set(next);
  }

  onDelete(card: FlashCard, event: MouseEvent) {
    event.stopPropagation();
    if (confirm('Delete this flashcard?')) {
      this.labService.deleteFlashcard(card.id).subscribe();
    }
  }

  onStartStudySession() {
    this.startStudy.emit({
      tag: this.selectedTag(),
      difficulty: this.selectedDifficulty(),
    });
  }

  getTagColor(tagName: string): string {
    const found = this.labService.tags().find((t) => t.name.toLowerCase() === tagName.toLowerCase());
    return found ? found.color : '#c25e2e';
  }
}
