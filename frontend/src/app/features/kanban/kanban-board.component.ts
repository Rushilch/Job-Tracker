import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  CdkDragDrop,
  DragDropModule,
  moveItemInArray,
  transferArrayItem,
} from '@angular/cdk/drag-drop';
import { ApplicationService } from '../../core/services/application.service';
import {
  Application,
  ApplicationCreate,
  ApplicationStatus,
} from '../../core/models/application.model';
import { ApplicationCardComponent } from './components/application-card.component';
import { CreateDialogComponent } from './components/create-dialog.component';

interface KanbanColumn {
  id: ApplicationStatus;
  title: string;
  badgeClass: string;
  items: Application[];
}

@Component({
  selector: 'app-kanban-board',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DragDropModule,
    ApplicationCardComponent,
    CreateDialogComponent,
  ],
  templateUrl: './kanban-board.component.html',
  styleUrls: ['./kanban-board.component.scss'],
})
export class KanbanBoardComponent implements OnInit {
  applicationService = inject(ApplicationService);

  searchQuery = signal<string>('');
  showCreateModal = signal<boolean>(false);
  selectedAppForDetail = signal<Application | null>(null);
  isTailoring = signal<boolean>(false);
  isUploading = signal<boolean>(false);
  copiedIndex = signal<number | null>(null);

  columnDefinitions: { id: ApplicationStatus; title: string; badgeClass: string }[] = [
    { id: 'discovered', title: 'Discovered', badgeClass: 'badge-discovered' },
    { id: 'applied', title: 'Applied', badgeClass: 'badge-applied' },
    { id: 'responded', title: 'Responded', badgeClass: 'badge-responded' },
    { id: 'interview_scheduled', title: 'Interviewing', badgeClass: 'badge-interview' },
    { id: 'offer', title: 'Offers', badgeClass: 'badge-offer' },
    { id: 'rejected', title: 'Rejected', badgeClass: 'badge-rejected' },
    { id: 'ghosted', title: 'Ghosted', badgeClass: 'badge-ghosted' },
  ];

  // Map connected drop lists for CDK
  connectedDropLists = computed(() =>
    this.columnDefinitions.map((col) => `list-${col.id}`)
  );

  // Group applications dynamically per status
  columns = computed<KanbanColumn[]>(() => {
    const apps = this.applicationService.applications();
    const query = this.searchQuery().toLowerCase().trim();

    return this.columnDefinitions.map((col) => {
      const filtered = apps
        .filter((a) => a.status === col.id)
        .filter((a) => {
          if (!query) return true;
          return (
            a.company.toLowerCase().includes(query) ||
            a.role.toLowerCase().includes(query) ||
            (a.tags && a.tags.some((t) => t.toLowerCase().includes(query)))
          );
        });

      return {
        ...col,
        items: filtered,
      };
    });
  });

  ngOnInit(): void {
    this.loadApplications();
  }

  loadApplications() {
    this.applicationService.loadApplications().subscribe();
  }

  onSearchChange(val: string) {
    this.searchQuery.set(val);
  }

  onExportExcel() {
    this.applicationService.exportExcel();
  }

  onDrop(event: CdkDragDrop<Application[]>, targetStatus: ApplicationStatus) {
    if (event.previousContainer === event.container) {
      moveItemInArray(
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );
    } else {
      const movedItem = event.previousContainer.data[event.previousIndex];
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );

      // Persist status change via API
      this.applicationService
        .updateStatus(movedItem.id, targetStatus)
        .subscribe({
          error: () => {
            // Revert state if backend call fails
            this.loadApplications();
          },
        });
    }
  }

  openCreateModal() {
    this.showCreateModal.set(true);
  }

  closeCreateModal() {
    this.showCreateModal.set(false);
  }

  handleCreateApplication(payload: ApplicationCreate) {
    this.applicationService.createApplication(payload).subscribe(() => {
      this.closeCreateModal();
    });
  }

  handleDeleteApplication(id: string) {
    if (confirm('Are you sure you want to delete this job application?')) {
      this.applicationService.deleteApplication(id).subscribe(() => {
        if (this.selectedAppForDetail()?.id === id) {
          this.closeDetailModal();
        }
      });
    }
  }

  handleSelectApplication(app: Application) {
    this.selectedAppForDetail.set(app);
  }

  closeDetailModal() {
    this.selectedAppForDetail.set(null);
  }

  onResumeFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    const app = this.selectedAppForDetail();
    if (!app) return;

    this.isUploading.set(true);
    this.applicationService.uploadResume(app.id, file).subscribe({
      next: (updated) => {
        this.isUploading.set(false);
        this.selectedAppForDetail.set(updated);
      },
      error: () => {
        this.isUploading.set(false);
        alert('Failed to upload resume file.');
      },
    });
  }

  triggerTailorResume() {
    const app = this.selectedAppForDetail();
    if (!app) return;

    this.isTailoring.set(true);
    this.applicationService.tailorApplicationResume(app.id).subscribe({
      next: (tailored) => {
        this.isTailoring.set(false);
        // Refresh detail view with updated tailored bullets
        this.applicationService.getApplication(app.id).subscribe((updated) => {
          this.selectedAppForDetail.set(updated);
        });
      },
      error: () => {
        this.isTailoring.set(false);
        alert('AI Resume Tailoring failed. Make sure the application has JD text.');
      },
    });
  }

  copyToClipboard(text: string, index?: number) {
    navigator.clipboard.writeText(text);
    if (index !== undefined) {
      this.copiedIndex.set(index);
      setTimeout(() => this.copiedIndex.set(null), 2000);
    } else {
      alert('Copied to clipboard!');
    }
  }
}
