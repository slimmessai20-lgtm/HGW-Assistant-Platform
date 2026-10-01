import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface User {
  id:         number;
  username:   string;
  full_name:  string;
  email:      string | null;
  role:       'admin' | 'engineer' | 'general';
  is_active:  number;
  created_at: string;
}

@Component({
  selector:    'app-admin-users',
  standalone:  true,
  imports:     [CommonModule, FormsModule],
  templateUrl: './admin-users.html',
  styleUrl:    './admin-users.scss'
})
export class AdminUsers implements OnInit {

  users:   User[] = [];
  loading  = true;

  // ── Modale création ─────────────────────────────────────────────────────────
  showModal = false;
  saving    = false;
  formError = '';
  form = { username: '', password: '', full_name: '', email: '', role: 'general' };

  constructor(
    private http: HttpClient,
    private zone: NgZone,
    private cdr:  ChangeDetectorRef
  ) {}

  ngOnInit() { this.loadUsers(); }

  // ── KPI helpers ──────────────────────────────────────────────────────────────
  get totalUsers()    { return this.users.length; }
  get adminCount()    { return this.users.filter(u => u.role === 'admin').length; }
  get engineerCount() { return this.users.filter(u => u.role === 'engineer').length; }
  get generalCount()  { return this.users.filter(u => !u.role || u.role === 'general').length; }
  get activeCount()   { return this.users.filter(u => u.is_active).length; }

  // ── API calls ────────────────────────────────────────────────────────────────
  loadUsers() {
    this.loading = true;
    this.http.get<User[]>('/api/auth/users').subscribe({
      next: data => this.zone.run(() => {
        this.users  = data;
        this.loading = false;
        this.cdr.detectChanges();
      }),
      error: () => this.zone.run(() => {
        this.loading = false;
        this.cdr.detectChanges();
      })
    });
  }

  openModal() {
    this.form      = { username: '', password: '', full_name: '', email: '', role: 'general' };
    this.formError = '';
    this.showModal = true;
  }

  closeModal() { this.showModal = false; }

  saveUser() {
    if (!this.form.username.trim() || !this.form.password.trim() || !this.form.full_name.trim()) {
      this.formError = 'Username, password and full name are required.';
      return;
    }
    this.saving    = true;
    this.formError = '';

    this.http.post('/api/auth/users', this.form).subscribe({
      next: () => this.zone.run(() => {
        this.saving    = false;
        this.showModal = false;
        this.loadUsers();
      }),
      error: (err) => this.zone.run(() => {
        this.saving    = false;
        this.formError = err?.error?.detail || 'Error creating user.';
        this.cdr.detectChanges();
      })
    });
  }

  toggleUser(user: User, event: Event) {
    event.stopPropagation();
    const newActive = !user.is_active;
    this.http.patch(`/api/auth/users/${user.id}/toggle?active=${newActive}`, {}).subscribe({
      next: () => this.zone.run(() => {
        user.is_active = newActive ? 1 : 0;
        this.cdr.detectChanges();
      }),
      error: () => alert('Error updating user status.')
    });
  }

  deleteUser(user: User, event: Event) {
    event.stopPropagation();
    if (!confirm(`Delete user "${user.username}"? This action is irreversible.`)) return;
    this.http.delete(`/api/auth/users/${user.id}`).subscribe({
      next: () => this.zone.run(() => {
        this.users = this.users.filter(u => u.id !== user.id);
        this.cdr.detectChanges();
      }),
      error: () => alert('Error deleting user.')
    });
  }

  // ── Display helpers ───────────────────────────────────────────────────────────
  roleLabel(role: string): string {
    return ({ admin: 'Admin', engineer: 'Engineer', general: 'General' } as any)[role] ?? role;
  }

  roleClass(role: string): string {
    return ({ admin: 'role-admin', engineer: 'role-engineer', general: 'role-general' } as any)[role] ?? '';
  }

  initials(name: string): string {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  }

  formatDate(iso: string): string {
    try {
      return new Date(iso).toLocaleString('fr-FR', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    } catch { return iso; }
  }
}
