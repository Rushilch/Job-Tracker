import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'kanban',
    loadComponent: () =>
      import('./features/kanban/kanban-board.component').then((m) => m.KanbanBoardComponent),
  },
  {
    path: 'jobs',
    loadComponent: () =>
      import('./features/discovery/job-discovery.component').then((m) => m.JobDiscoveryComponent),
  },
  {
    path: 'checker',
    loadComponent: () =>
      import('./features/checker/match-checker.component').then((m) => m.MatchCheckerComponent),
  },
  {
    path: 'interview-lab',
    loadComponent: () =>
      import('./features/interview/interview-lab.component').then((m) => m.InterviewLabComponent),
  },
  {
    path: '**',
    redirectTo: 'kanban',
  },
];
