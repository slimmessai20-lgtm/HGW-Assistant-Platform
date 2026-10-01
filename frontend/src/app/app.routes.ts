import { Routes } from '@angular/router';
import { authGuard, adminGuard, engineerGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'auth/login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/auth/login/login').then(m => m.Login)
  },
  {
    path: 'auth/login',
    loadComponent: () =>
      import('./pages/auth/login/login').then(m => m.Login)
  },
  {
    path: 'auth/reset-password',
    loadComponent: () =>
      import('./pages/auth/reset-password/reset-password').then(m => m.ResetPassword)
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./layout/main-layout/main-layout').then(m => m.MainLayout),
    children: [
      {
        path: '',
        loadComponent: () =>
          import('./pages/dashboard/dashboard').then(m => m.Dashboard)
      },
      {
        path: 'chat',
        loadComponent: () =>
          import('./pages/chat/chat').then(m => m.Chat)
      },
      {
        path: 'entries',
        canActivate: [engineerGuard],
        loadComponent: () =>
          import('./pages/entries/entries-list').then(m => m.EntriesList)
      },
      {
        path: 'entries/add',
        canActivate: [engineerGuard],
        loadComponent: () =>
          import('./pages/entries/entries-add').then(m => m.EntriesAdd)
      },
      {
        path: 'entries/:id/edit',
        canActivate: [engineerGuard],
        loadComponent: () =>
          import('./pages/entries/entries-add').then(m => m.EntriesAdd)
      },
      {
        path: 'entries/:id',
        canActivate: [engineerGuard],
        loadComponent: () =>
          import('./pages/entries/entry-detail').then(m => m.EntryDetail)
      },
      {
        path: 'admin/users',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./pages/admin/admin-users').then(m => m.AdminUsers)
      },
      {
        path: 'admin/requests',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./pages/admin/admin-requests').then(m => m.AdminRequests)
      },
      {
        path: 'admin/conversations',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./pages/admin/admin-conversations').then(m => m.AdminConversations)
      },
      {
        path: 'admin/prompts',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./pages/admin/admin-prompts').then(m => m.AdminPrompts)
      },
      {
        path: 'admin/analytics',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./pages/admin/admin-stats').then(m => m.AdminStats)
      },
      {
        path: 'profile',
        loadComponent: () =>
          import('./pages/profile/profile').then(m => m.Profile)
      },
      {
        path: '**',
        redirectTo: ''
      }
    ]
  },
  {
    path: '**',
    redirectTo: 'auth/login'
  }
];