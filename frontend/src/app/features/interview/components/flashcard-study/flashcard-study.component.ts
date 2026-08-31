import { Component, EventEmitter, HostListener, Input, OnInit, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../../../core/services/interview-lab.service';
import { FlashCard } from '../../../../core/models/interview-lab.model';

@Component({
  selector: 'app-flashcard-study',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './flashcard-study.component.html',
  styleUrls: ['./flashcard-study.component.scss'],
})
export class FlashcardStudyComponent implements OnInit {
  labService = inject(InterviewLabService);

  @Input() initialTag: string = 'All';
  @Input() initialDifficulty: string = 'All';
  @Output() exited = new EventEmitter<void>();

  deck = signal<FlashCard[]>([]);
  currentIndex = signal<number>(0);
  isFlipped = signal<boolean>(false);
  isShuffle = signal<boolean>(true);
  isSessionComplete = signal<boolean>(false);

  selectedTag = signal<string>('All');
  selectedDifficulty = signal<string>('All');

  // Keyboard navigation
  @HostListener('window:keydown', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent) {
    if (event.key === ' ' || event.code === 'Space') {
      event.preventDefault();
      this.flipCard();
    } else if (event.key === 'ArrowRight') {
      this.nextCard();
    } else if (event.key === 'ArrowLeft') {
      this.prevCard();
    } else if (event.key === 'Escape') {
      this.exit();
    }
  }

  ngOnInit(): void {
    this.selectedTag.set(this.initialTag);
    this.selectedDifficulty.set(this.initialDifficulty);
    this.loadDeck();
  }

  loadDeck() {
    this.labService.getStudyDeck({
      count: 50,
      tag: this.selectedTag(),
      difficulty: this.selectedDifficulty(),
      shuffle: this.isShuffle(),
    }).subscribe({
      next: (cards) => {
        this.deck.set(cards);
        this.currentIndex.set(0);
        this.isFlipped.set(false);
        this.isSessionComplete.set(false);
      },
    });
  }

  flipCard() {
    this.isFlipped.set(!this.isFlipped());
  }

  nextCard() {
    if (this.currentIndex() < this.deck().length - 1) {
      this.currentIndex.update((i) => i + 1);
      this.isFlipped.set(false);
    } else if (this.deck().length > 0) {
      this.isSessionComplete.set(true);
    }
  }

  prevCard() {
    if (this.currentIndex() > 0) {
      this.currentIndex.update((i) => i - 1);
      this.isFlipped.set(false);
    }
  }

  restartSession() {
    this.currentIndex.set(0);
    this.isFlipped.set(false);
    this.isSessionComplete.set(false);
    if (this.isShuffle()) {
      const shuffled = [...this.deck()].sort(() => Math.random() - 0.5);
      this.deck.set(shuffled);
    }
  }

  toggleShuffle() {
    this.isShuffle.set(!this.isShuffle());
    this.loadDeck();
  }

  getTagColor(tagName: string): string {
    const found = this.labService.tags().find((t) => t.name.toLowerCase() === tagName.toLowerCase());
    return found ? found.color : '#c25e2e';
  }

  exit() {
    this.exited.emit();
  }
}
