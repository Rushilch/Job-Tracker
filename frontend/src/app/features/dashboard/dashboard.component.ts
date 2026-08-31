import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApplicationService } from '../../core/services/application.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit {
  applicationService = inject(ApplicationService);
  isExporting = false;

  ngOnInit(): void {
    this.applicationService.loadApplications().subscribe();
    this.applicationService.loadStats().subscribe();
  }

  onExportExcel() {
    this.isExporting = true;
    this.applicationService.exportExcel();
    setTimeout(() => {
      this.isExporting = false;
    }, 1500);
  }

  getRecentApplications() {
    return this.applicationService.applications().slice(0, 5);
  }

  getTailoredCount(): number {
    return this.applicationService.applications().filter((a) => !!a.tailored_resume_summary || !!a.resume_filename).length;
  }
}
