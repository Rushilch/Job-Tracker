import { Component, EventEmitter, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApplicationCreate, ApplicationStatus } from '../../../core/models/application.model';
import { ApplicationService } from '../../../core/services/application.service';

@Component({
  selector: 'app-create-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './create-dialog.component.html',
  styleUrls: ['./create-dialog.component.scss'],
})
export class CreateDialogComponent {
  @Output() close = new EventEmitter<void>();
  @Output() create = new EventEmitter<ApplicationCreate>();

  form: FormGroup;
  isScraping = signal<boolean>(false);
  isSubmitting = signal<boolean>(false);
  inlineMessage = signal<{ type: 'error' | 'success'; text: string } | null>(null);

  statusOptions: { label: string; value: ApplicationStatus }[] = [
    { label: 'Discovered', value: 'discovered' },
    { label: 'Applied', value: 'applied' },
    { label: 'Responded', value: 'responded' },
    { label: 'Interview Scheduled', value: 'interview_scheduled' },
    { label: 'Offer Received', value: 'offer' },
    { label: 'Rejected', value: 'rejected' },
    { label: 'Ghosted', value: 'ghosted' },
  ];

  constructor(
    private fb: FormBuilder,
    private applicationService: ApplicationService
  ) {
    this.form = this.fb.group({
      company: ['', [Validators.required]],
      role: ['', [Validators.required]],
      job_url: [''],
      location: ['Remote'],
      salary_range: [''],
      status: ['applied'],
      tagsInput: ['Python, FastAPI'],
      notes: [''],
      jd_snapshot: [''],
    });
  }

  onAutoFillFromUrl() {
    const url = this.form.get('job_url')?.value;
    if (!url || !url.startsWith('http')) {
      this.inlineMessage.set({ type: 'error', text: 'Please enter a valid job URL starting with http:// or https://' });
      return;
    }

    this.isScraping.set(true);
    this.inlineMessage.set(null);

    this.applicationService.scrapeJobUrl(url).subscribe({
      next: (res) => {
        this.isScraping.set(false);
        if (res.status === 'success') {
          if (res.title && !this.form.get('role')?.value) {
            this.form.patchValue({ role: res.title });
          }
          if (res.company && !this.form.get('company')?.value) {
            this.form.patchValue({ company: res.company });
          }
          if (res.jd_text) {
            this.form.patchValue({ jd_snapshot: res.jd_text });
          }
          this.inlineMessage.set({ type: 'success', text: 'Extracted job title, company, and JD snapshot successfully!' });
        } else {
          this.inlineMessage.set({ type: 'error', text: 'Could not auto-extract details: ' + res.message });
        }
      },
      error: () => {
        this.isScraping.set(false);
        this.inlineMessage.set({ type: 'error', text: 'Web scraping service unavailable. Please enter details manually.' });
      },
    });
  }

  onSubmit() {
    if (this.form.invalid) return;

    this.isSubmitting.set(true);
    const val = this.form.value;
    const tags = val.tagsInput
      ? val.tagsInput.split(',').map((t: string) => t.trim()).filter((t: string) => t.length > 0)
      : [];

    const payload: ApplicationCreate = {
      company: val.company,
      role: val.role,
      job_url: val.job_url || null,
      location: val.location || null,
      salary_range: val.salary_range || null,
      status: val.status,
      tags,
      notes: val.notes || null,
      jd_snapshot: val.jd_snapshot || null,
    };

    this.create.emit(payload);
  }

  onCancel() {
    this.close.emit();
  }
}
