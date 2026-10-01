import { Component, inject, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { LayoutService } from '../../services/layout.service';
import { AuthService } from '../../services/auth.service';

interface NotifItem {
  id: number;
  username: string | null;
  message: string;
  voice_used: number;
  created_at: string;
}

@Component({
  selector: 'app-topbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './topbar.html',
  styleUrl: './topbar.scss'
})
export class Topbar implements OnInit {
  layout = inject(LayoutService);
  auth   = inject(AuthService);
  private http   = inject(HttpClient);
  private router = inject(Router);

  isDark       = true;
  showUserMenu = false;
  showNotifs   = false;
  notifItems:  NotifItem[] = [];
  notifUnread  = 0;

  ngOnInit() {
    const saved = localStorage.getItem('app-theme');
    if (saved === 'light') {
      this.isDark = false;
      document.body.classList.add('app-light');
    }
    if (this.auth.getRole() === 'admin') {
      this.loadNotifs();
    }
  }

  get currentUser() {
    return {
      username: this.auth.getUsername(),
      role:     this.auth.getRole()
    };
  }

  get userInitials(): string {
    const name = this.auth.getUsername() ?? '';
    return name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2) || '?';
  }

  toggleDark(): void {
    this.isDark = !this.isDark;
    document.body.classList.toggle('app-light', !this.isDark);
    localStorage.setItem('app-theme', this.isDark ? 'dark' : 'light');
  }

  toggleNotifs(): void {
    this.showNotifs   = !this.showNotifs;
    this.showUserMenu = false;
    if (this.showNotifs) this.notifUnread = 0;
  }

  toggleUserMenu(): void {
    this.showUserMenu = !this.showUserMenu;
    this.showNotifs   = false;
  }

  loadNotifs() {
    this.http.get<NotifItem[]>('/api/chat-logs?limit=6').subscribe({
      next: items => {
        this.notifItems  = items;
        this.notifUnread = items.length;
      },
      error: () => {}
    });
  }

  goToLogs() {
    this.showNotifs = false;
    this.router.navigate(['/dashboard/admin/conversations']);
  }

  goToProfile() {
    this.showUserMenu = false;
    this.router.navigate(['/dashboard/profile']);
  }

  goToSettings() {
    this.showUserMenu = false;
    this.router.navigate(['/dashboard/admin/prompts']);
  }

  get isAdmin(): boolean {
    return this.auth.getRole() === 'admin';
  }

  formatTime(iso: string): string {
    const diff = Date.now() - new Date(iso).getTime();
    const m = Math.floor(diff / 60000);
    if (m < 1)  return 'just now';
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
  }

  @HostListener('document:click', ['$event'])
  onDocClick(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (!target.closest('.notif-wrap') && !target.closest('.user-wrap')) {
      this.showNotifs   = false;
      this.showUserMenu = false;
    }
  }

  logout(): void {
    this.auth.logout();
  }
}
