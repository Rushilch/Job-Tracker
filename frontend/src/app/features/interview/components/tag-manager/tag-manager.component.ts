import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { InterviewLabService } from '../../../../core/services/interview-lab.service';
import { Tag } from '../../../../core/models/interview-lab.model';

@Component({
  selector: 'app-tag-manager',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './tag-manager.component.html',
  styleUrls: ['./tag-manager.component.scss'],
})
export class TagManagerComponent {
  labService = inject(InterviewLabService);

  @Output() closed = new EventEmitter<void>();

  newTagName = signal<string>('');
  newTagColor = signal<string>('#c25e2e');
  isSubmitting = signal<boolean>(false);

  presetColors = [
    '#c25e2e', // Terracotta
    '#386641', // Sage / Forest
    '#284b63', // Vintage Navy
    '#d97706', // Amber
    '#bc4749', // Brick Red
    '#6b21a8', // Purple
    '#0f766e', // Teal
    '#475569', // Slate
  ];

  selectColor(color: string) {
    this.newTagColor.set(color);
  }

  onAddTag() {
    const name = this.newTagName().trim();
    if (!name) return;

    this.isSubmitting.set(true);
    this.labService.createTag({ name, color: this.newTagColor() }).subscribe({
      next: () => {
        this.newTagName.set('');
        this.isSubmitting.set(false);
      },
      error: () => this.isSubmitting.set(false),
    });
  }

  onDeleteTag(tag: Tag, event: MouseEvent) {
    event.stopPropagation();
    if (confirm(`Delete tag "${tag.name}"?`)) {
      this.labService.deleteTag(tag.id).subscribe();
    }
  }

  close() {
    this.closed.emit();
  }
}
