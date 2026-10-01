import { Component, inject, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './profile.html',
  styleUrl: './profile.scss'
})
export class Profile {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private zone = inject(NgZone);
  private cdr  = inject(ChangeDetectorRef);

  currentPassword = '';
  newPassword     = '';
  confirmPassword = '';

  loading  = false;
  success  = false;
  errorMsg = '';

  get user() { return this.auth.getUser(); }

  get roleLabel(): string {
    return ({ admin: 'Admin', engineer: 'Engineer', general: 'General' } as any)[this.user?.role ?? ''] ?? '—';
  }

  get roleClass(): string {
    return ({ admin: 'role-admin', engineer: 'role-engineer', general: 'role-general' } as any)[this.user?.role ?? ''] ?? '';
  }

  get roleIcon(): string {
    return ({ admin: 'pi-shield', engineer: 'pi-wrench', general: 'pi-user' } as any)[this.user?.role ?? ''] ?? 'pi-user';
  }

  get initials(): string {
    const name = this.user?.username ?? '';
    return name.slice(0, 2).toUpperCase() || '?';
  }

  changePassword() {
    this.errorMsg = '';
    this.success  = false;

    if (!this.currentPassword || !this.newPassword || !this.confirmPassword) {
      this.errorMsg = 'Please fill in all fields.'; return;
    }
    if (this.newPassword.length < 8) {
      this.errorMsg = 'New password must be at least 8 characters.'; return;
    }
    if (this.newPassword !== this.confirmPassword) {
      this.errorMsg = 'New passwords do not match.'; return;
    }

    this.loading = true;
    this.http.post('/api/auth/change-password', {
      current_password: this.currentPassword,
      new_password:     this.newPassword
    }).subscribe({
      next: () => this.zone.run(() => {
        this.success         = true;
        this.loading         = false;
        this.currentPassword = '';
        this.newPassword     = '';
        this.confirmPassword = '';
        this.cdr.detectChanges();
        setTimeout(() => { this.success = false; this.cdr.detectChanges(); }, 4000);
      }),
      error: (err) => this.zone.run(() => {
        this.errorMsg = err?.error?.detail ?? 'An error occurred. Please try again.';
        this.loading  = false;
        this.cdr.detectChanges();
      })
    });
  }
}
