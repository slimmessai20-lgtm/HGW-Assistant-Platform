import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

export interface UserInfo {
  id: number;
  username: string;
  full_name: string;
  email: string;
  role: 'admin' | 'engineer' | 'general';
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

// ── Authentication Service avec Observable Pattern ────────────────────────────

@Injectable({ providedIn: 'root' })
export class AuthService {
  private authToken = signal<string | null>(null);
  private userRole = signal<'general' | 'engineer' | 'admin' | null>(null);
  private userId = signal<number | null>(null);
  private username = signal<string | null>(null);
  private userFullName = signal<string | null>(null);

  constructor(private http: HttpClient, private router: Router) {
    this.loadFromStorage();
  }

  private loadFromStorage() {
    // ✅ Restaure la session depuis localStorage
    const token = localStorage.getItem('auth_token');
    const role = localStorage.getItem('user_role');
    const id = localStorage.getItem('user_id');
    const name = localStorage.getItem('username');
    const fullName = localStorage.getItem('user_full_name');

    if (token) {
      this.authToken.set(token);
      this.userRole.set(role as any);
      this.userId.set(id ? parseInt(id) : null);
      this.username.set(name);
      this.userFullName.set(fullName);
    }
  }

  // ── Login avec Observable Pattern ────────────────────────────────────────────
  login(username: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>('/api/auth/login', { username, password }).pipe(
      tap((res) => {
        // ✅ Stocke les données de session
        localStorage.setItem('auth_token', res.access_token);
        localStorage.setItem('user_role', res.user.role);
        localStorage.setItem('user_id', res.user.id.toString());
        localStorage.setItem('username', res.user.username);
        localStorage.setItem('user_full_name', res.user.full_name);

        // ✅ Mets à jour les signals
        this.authToken.set(res.access_token);
        this.userRole.set(res.user.role as any);
        this.userId.set(res.user.id);
        this.username.set(res.user.username);
        this.userFullName.set(res.user.full_name);
      })
    );
  }

  // ── Getters (les signals peuvent être accédés directement dans les templates) ──

  getToken() {
    return this.authToken();
  }

  getRole() {
    return this.userRole();
  }

  getUserId() {
    return this.userId();
  }

  getUsername() {
    return this.username();
  }

  getUser(): UserInfo | null {
    const token = this.authToken();
    if (!token) return null;

    return {
      id: this.userId() || 0,
      username: this.username() || '',
      full_name: this.userFullName() || '',
      email: '',
      role: this.userRole() || 'general',
      is_active: true
    };
  }

  isAuthenticated() {
    return !!this.authToken();
  }

  isAdmin() {
    return this.userRole() === 'admin';
  }

  isEngineer() {
    return this.userRole() === 'engineer' || this.userRole() === 'admin';
  }

  // ── Eligibilité pour la vue technique ────────────────────────────────────────
  getTechnicalViewEnabled() {
    // ✅ Les ingénieurs et admins voient les réponses techniques
    return this.isEngineer();
  }

  // ── Logout ───────────────────────────────────────────────────────────────────

  logout() {
    // ✅ Efface le stockage et réinitialise les signals
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    localStorage.removeItem('user_full_name');

    this.authToken.set(null);
    this.userRole.set(null);
    this.userId.set(null);
    this.username.set(null);
    this.userFullName.set(null);

    this.router.navigate(['/login']);
  }
}

