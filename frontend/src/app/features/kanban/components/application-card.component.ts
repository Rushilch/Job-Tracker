import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Application } from '../../../core/models/application.model';

@Component({
  selector: 'app-application-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './application-card.component.html',
  styleUrls: ['./application-card.component.scss'],
})
export class ApplicationCardComponent {
  @Input({ required: true }) application!: Application;
  @Output() delete = new EventEmitter<string>();
  @Output() select = new EventEmitter<Application>();

  getDaysSinceDiscovered(): number {
    const discovered = new Date(this.application.date_discovered).getTime();
    const now = new Date().getTime();
    const diff = Math.floor((now - discovered) / (1000 * 60 * 60 * 24));
    return diff;
  }

  onCardClick(event: MouseEvent) {
    this.select.emit(this.application);
  }

  onDeleteClick(event: MouseEvent) {
    event.stopPropagation();
    this.delete.emit(this.application.id);
  }
}
