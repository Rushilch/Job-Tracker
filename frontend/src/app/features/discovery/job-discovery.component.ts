import { Component, OnInit, OnDestroy, signal, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService, DiscoveredJob } from '../../core/services/agent.service';

@Component({
  selector: 'app-job-discovery',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './job-discovery.component.html',
  styleUrls: ['./job-discovery.component.scss'],
})
export class JobDiscoveryComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('scrollAnchor') scrollAnchor?: ElementRef<HTMLDivElement>;

  searchQuery = signal<string>('Software Engineer');
  locationQuery = signal<string>('Remote');
  sourceFilter = signal<string>('all');
  jobTypeFilter = signal<string>('all');
  sortBy = signal<string>('relevance');

  currentPage = signal<number>(1);
  pageSize = signal<number>(30);
  isLoading = signal<boolean>(false);
  isLoadingMore = signal<boolean>(false);
  hasMore = signal<boolean>(true);
  isInfiniteScroll = signal<boolean>(true);
  isExporting = signal<boolean>(false);

  showAddSiteModal = signal<boolean>(false);
  isAddingSite = signal<boolean>(false);
  newSiteName = signal<string>('');
  newSiteType = signal<string>('greenhouse');
  jobs = signal<DiscoveredJob[]>([]);
  trackedIds = signal<Set<string>>(new Set());
  trackingJobId = signal<string | null>(null);

  private observer?: IntersectionObserver;

  filterTags: string[] = [
    'Software Engineer',
    'Python',
    'FastAPI',
    'Backend',
    'Full Stack',
    'Angular',
    'React',
    'AI / ML',
    'DevOps',
    'Golang',
    'Java',
    'C# / .NET',
  ];

  locationOptions: string[] = ['Remote', 'United States', 'India', 'UK / Europe', 'Canada', 'Worldwide'];

  sources: { id: string; label: string }[] = [
    { id: 'all', label: '🌟 All Sources (JobSpy + Career Pages + Remote Feeds)' },
    { id: 'jobspy', label: '🚀 JobSpy Multi-Board (Indeed, LinkedIn, Glassdoor, ZipRecruiter, Google)' },
    { id: 'indeed', label: '💼 Indeed (JobSpy Engine)' },
    { id: 'linkedin', label: '👔 LinkedIn (JobSpy Engine)' },
    { id: 'glassdoor', label: '🏢 Glassdoor (JobSpy Engine)' },
    { id: 'zip_recruiter', label: '⚡ ZipRecruiter (JobSpy Engine)' },
    { id: 'google', label: '🔍 Google Jobs (JobSpy Engine)' },
    { id: 'career_pages', label: '🏢 Official Career Pages (Stripe, Figma, Databricks, Canva, Spotify...)' },
    { id: 'remoteok', label: '🌐 RemoteOK API' },
    { id: 'remotive', label: '⚡ Remotive API' },
    { id: 'weworkremotely', label: '💻 WeWorkRemotely' },
  ];

  jobTypes: { id: string; label: string }[] = [
    { id: 'all', label: 'All Job Types' },
    { id: 'fulltime', label: 'Full-Time' },
    { id: 'contract', label: 'Contract / Freelance' },
    { id: 'internship', label: 'Internship' },
    { id: 'parttime', label: 'Part-Time' },
  ];

  pageSizes: number[] = [20, 30, 50, 100];

  constructor(public agentService: AgentService) {}

  ngOnInit(): void {
    this.agentService.loadModels().subscribe();
    this.agentService.getCareerSites().subscribe();
    this.onSearchJobs(true);
  }

  ngAfterViewInit(): void {
    this.initIntersectionObserver();
  }

  ngOnDestroy(): void {
    if (this.observer) {
      this.observer.disconnect();
    }
  }

  private initIntersectionObserver() {
    if (typeof IntersectionObserver === 'undefined') return;

    this.observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting && this.isInfiniteScroll() && !this.isLoading() && !this.isLoadingMore() && this.hasMore() && this.jobs().length > 0) {
          this.onLoadNextPage();
        }
      },
      { rootMargin: '300px' }
    );

    if (this.scrollAnchor?.nativeElement) {
      this.observer.observe(this.scrollAnchor.nativeElement);
    }
  }

  onSelectQuickTag(tag: string) {
    this.searchQuery.set(tag);
    this.onSearchJobs(true);
  }

  onSelectLocation(loc: string) {
    this.locationQuery.set(loc);
    this.onSearchJobs(true);
  }

  onSelectSource(src: string) {
    this.sourceFilter.set(src);
    this.onSearchJobs(true);
  }

  onSearchJobs(reset = true) {
    if (reset) {
      this.currentPage.set(1);
      this.hasMore.set(true);
      this.isLoading.set(true);
    }

    this.agentService.discoverJobs(
      this.searchQuery(),
      this.locationQuery(),
      this.sourceFilter(),
      this.currentPage(),
      this.pageSize()
    ).subscribe({
      next: (data) => {
        this.isLoading.set(false);
        this.isLoadingMore.set(false);
        if (reset) {
          this.jobs.set(data);
        } else {
          // Append and deduplicate
          const current = this.jobs();
          const existingIds = new Set(current.map((j) => j.id));
          const newJobs = data.filter((j) => !existingIds.has(j.id));
          this.jobs.set([...current, ...newJobs]);
        }
        if (data.length < 5) {
          this.hasMore.set(false);
        }
      },
      error: () => {
        this.isLoading.set(false);
        this.isLoadingMore.set(false);
      },
    });
  }

  onLoadNextPage() {
    if (this.isLoading() || this.isLoadingMore() || !this.hasMore()) return;

    this.isLoadingMore.set(true);
    this.currentPage.update((p) => p + 1);
    this.onSearchJobs(false);
  }

  onPageSizeChange(size: number) {
    this.pageSize.set(size);
    this.onSearchJobs(true);
  }

  onToggleInfiniteScroll() {
    this.isInfiniteScroll.update((v) => !v);
  }

  onAddNewCareerSite() {
    if (!this.newSiteName().trim()) return;

    this.isAddingSite.set(true);
    this.agentService.addCareerSite(this.newSiteName(), this.newSiteType()).subscribe({
      next: () => {
        this.isAddingSite.set(false);
        this.showAddSiteModal.set(false);
        this.newSiteName.set('');
        this.sourceFilter.set('career_pages');
        this.onSearchJobs(true);
      },
      error: () => {
        this.isAddingSite.set(false);
        alert('Failed to add custom career site.');
      },
    });
  }

  onExportExcel() {
    this.isExporting.set(true);
    this.agentService.exportDiscoveredJobsExcel(
      this.searchQuery(),
      this.locationQuery(),
      this.sourceFilter(),
      Math.max(this.jobs().length, 50)
    ).subscribe({
      next: (blob) => {
        this.isExporting.set(false);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const cleanName = this.searchQuery().replace(/\s+/g, '_').toLowerCase();
        a.download = `careerpilot_jobs_${cleanName}_p${this.currentPage()}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      },
      error: () => {
        this.isExporting.set(false);
        alert('Failed to generate Excel export.');
      },
    });
  }

  onTrackJob(job: DiscoveredJob) {
    this.trackingJobId.set(job.id);
    this.agentService.trackDiscoveredJob(job).subscribe({
      next: () => {
        this.trackingJobId.set(null);
        const next = new Set(this.trackedIds());
        next.add(job.id);
        this.trackedIds.set(next);
      },
      error: () => {
        this.trackingJobId.set(null);
        alert('Failed to track job into Kanban.');
      },
    });
  }
}
