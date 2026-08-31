import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../core/services/interview-lab.service';
import { ApplicationService } from '../../core/services/application.service';
import { Application } from '../../core/models/application.model';
import {
  Experience,
  FlashCard,
  Question,
} from '../../core/models/interview-lab.model';
import { QuestionListComponent } from './components/question-list/question-list.component';
import { QuestionEditorComponent } from './components/question-editor/question-editor.component';
import { ExperienceListComponent } from './components/experience-list/experience-list.component';
import { ExperienceEditorComponent } from './components/experience-editor/experience-editor.component';
import { FlashcardListComponent } from './components/flashcard-list/flashcard-list.component';
import { FlashcardEditorComponent } from './components/flashcard-editor/flashcard-editor.component';
import { FlashcardStudyComponent } from './components/flashcard-study/flashcard-study.component';
import { TagManagerComponent } from './components/tag-manager/tag-manager.component';

export type LabTab = 'questions' | 'experiences' | 'flashcards';

@Component({
  selector: 'app-interview-lab',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    QuestionListComponent,
    QuestionEditorComponent,
    ExperienceListComponent,
    ExperienceEditorComponent,
    FlashcardListComponent,
    FlashcardEditorComponent,
    FlashcardStudyComponent,
    TagManagerComponent,
  ],
  templateUrl: './interview-lab.component.html',
  styleUrls: ['./interview-lab.component.scss'],
})
export class InterviewLabComponent implements OnInit {
  labService = inject(InterviewLabService);
  appService = inject(ApplicationService);

  activeTab = signal<LabTab>('questions');

  // Selected Role / Job Application from tracked pipeline (empty by default)
  selectedApplication = signal<Application | null>(null);

  // Modal display states
  showTagManager = signal<boolean>(false);
  showQuestionEditor = signal<boolean>(false);
  questionToEdit = signal<Question | null>(null);

  showExperienceEditor = signal<boolean>(false);
  experienceToEdit = signal<Experience | null>(null);

  showFlashcardEditor = signal<boolean>(false);
  cardToEdit = signal<FlashCard | null>(null);

  showStudyMode = signal<boolean>(false);
  studyTag = signal<string>('All');
  studyDifficulty = signal<string>('All');

  ngOnInit(): void {
    // Load tags and list of tracked applications
    this.labService.loadTags().subscribe();
    this.appService.loadApplications().subscribe();
  }

  selectRole(app: Application | null) {
    this.selectedApplication.set(app);
    if (app) {
      this.labService.loadQuestions({ applicationId: app.id, company: app.company }).subscribe();
      this.labService.loadExperiences({ applicationId: app.id, company: app.company }).subscribe();
      this.labService.loadFlashcards({ applicationId: app.id, company: app.company }).subscribe();
    } else {
      this.labService.questions.set([]);
      this.labService.experiences.set([]);
      this.labService.flashcards.set([]);
    }
  }

  onRoleSelect(appId: string) {
    if (!appId) {
      this.selectRole(null);
      return;
    }
    const found = this.appService.applications().find((a) => a.id === appId) || null;
    this.selectRole(found);
  }

  setTab(tab: LabTab) {
    this.activeTab.set(tab);
  }

  exportExcel() {
    const app = this.selectedApplication();
    this.labService.exportExcel(app?.id, app?.company);
  }

  // --- Question Actions ---
  openAddQuestion() {
    this.questionToEdit.set(null);
    this.showQuestionEditor.set(true);
  }

  openEditQuestion(q: Question) {
    this.questionToEdit.set(q);
    this.showQuestionEditor.set(true);
  }

  onQuestionSaved() {
    this.showQuestionEditor.set(false);
    this.questionToEdit.set(null);
    const app = this.selectedApplication();
    this.labService.loadQuestions({ applicationId: app?.id, company: app?.company }).subscribe();
  }

  // --- Experience Actions ---
  openAddExperience() {
    this.experienceToEdit.set(null);
    this.showExperienceEditor.set(true);
  }

  openEditExperience(exp: Experience) {
    this.experienceToEdit.set(exp);
    this.showExperienceEditor.set(true);
  }

  onExperienceSaved() {
    this.showExperienceEditor.set(false);
    this.experienceToEdit.set(null);
    const app = this.selectedApplication();
    this.labService.loadExperiences({ applicationId: app?.id, company: app?.company }).subscribe();
  }

  // --- Flashcard Actions ---
  openAddFlashcard() {
    this.cardToEdit.set(null);
    this.showFlashcardEditor.set(true);
  }

  openEditFlashcard(card: FlashCard) {
    this.cardToEdit.set(card);
    this.showFlashcardEditor.set(true);
  }

  onFlashcardSaved() {
    this.showFlashcardEditor.set(false);
    this.cardToEdit.set(null);
    const app = this.selectedApplication();
    this.labService.loadFlashcards({ applicationId: app?.id, company: app?.company }).subscribe();
  }

  // --- Study Mode ---
  startStudySession(event: { tag: string; difficulty: string }) {
    this.studyTag.set(event.tag);
    this.studyDifficulty.set(event.difficulty);
    this.showStudyMode.set(true);
  }
}
