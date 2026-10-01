import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { AuthService, LoginResponse } from './auth.service';

const MOCK_LOGIN_RESPONSE: LoginResponse = {
  access_token: 'mock.jwt.token',
  token_type: 'bearer',
  user: {
    id: 1,
    username: 'admin',
    full_name: 'Admin User',
    email: 'admin@test.com',
    role: 'admin',
    is_active: true
  }
};

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([])
      ]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  // ── Initial state ───────────────────────────────────────────────────────────

  it('should create the service', () => {
    expect(service).toBeTruthy();
  });

  it('should not be authenticated on fresh start', () => {
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('should return null role when not logged in', () => {
    expect(service.getRole()).toBeNull();
  });

  it('should return null username when not logged in', () => {
    expect(service.getUsername()).toBeNull();
  });

  it('should return null token when not logged in', () => {
    expect(service.getToken()).toBeNull();
  });

  // ── Login ───────────────────────────────────────────────────────────────────

  it('should call POST /api/auth/login on login()', () => {
    service.login('admin', 'password').subscribe();
    const req = httpMock.expectOne('/api/auth/login');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ username: 'admin', password: 'password' });
    req.flush(MOCK_LOGIN_RESPONSE);
  });

  it('should store token in localStorage after login', (done) => {
    service.login('admin', 'password').subscribe(() => {
      expect(localStorage.getItem('auth_token')).toBe('mock.jwt.token');
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(MOCK_LOGIN_RESPONSE);
  });

  it('should set isAuthenticated() to true after login', (done) => {
    service.login('admin', 'password').subscribe(() => {
      expect(service.isAuthenticated()).toBeTrue();
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(MOCK_LOGIN_RESPONSE);
  });

  it('should set role to admin after admin login', (done) => {
    service.login('admin', 'password').subscribe(() => {
      expect(service.getRole()).toBe('admin');
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(MOCK_LOGIN_RESPONSE);
  });

  it('should set username after login', (done) => {
    service.login('admin', 'password').subscribe(() => {
      expect(service.getUsername()).toBe('admin');
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(MOCK_LOGIN_RESPONSE);
  });

  // ── Role checks ─────────────────────────────────────────────────────────────

  it('isAdmin() should return true when role is admin', (done) => {
    service.login('admin', 'password').subscribe(() => {
      expect(service.isAdmin()).toBeTrue();
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(MOCK_LOGIN_RESPONSE);
  });

  it('isAdmin() should return false when role is general', (done) => {
    const generalResponse = {
      ...MOCK_LOGIN_RESPONSE,
      user: { ...MOCK_LOGIN_RESPONSE.user, role: 'general' as const }
    };
    service.login('user', 'password').subscribe(() => {
      expect(service.isAdmin()).toBeFalse();
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(generalResponse);
  });

  it('isEngineer() should return true when role is engineer', (done) => {
    const engineerResponse = {
      ...MOCK_LOGIN_RESPONSE,
      user: { ...MOCK_LOGIN_RESPONSE.user, role: 'engineer' as const }
    };
    service.login('eng', 'password').subscribe(() => {
      expect(service.isEngineer()).toBeTrue();
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(engineerResponse);
  });

  it('isEngineer() should return true when role is admin', (done) => {
    service.login('admin', 'password').subscribe(() => {
      expect(service.isEngineer()).toBeTrue();
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(MOCK_LOGIN_RESPONSE);
  });

  // ── Logout ──────────────────────────────────────────────────────────────────

  it('should clear localStorage on logout', (done) => {
    service.login('admin', 'password').subscribe(() => {
      service.logout();
      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(localStorage.getItem('user_role')).toBeNull();
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(MOCK_LOGIN_RESPONSE);
  });

  it('should set isAuthenticated() to false after logout', (done) => {
    service.login('admin', 'password').subscribe(() => {
      service.logout();
      expect(service.isAuthenticated()).toBeFalse();
      done();
    });
    httpMock.expectOne('/api/auth/login').flush(MOCK_LOGIN_RESPONSE);
  });

  // ── Session restore ─────────────────────────────────────────────────────────

  it('should restore session from localStorage on init', () => {
    localStorage.setItem('auth_token', 'stored.token');
    localStorage.setItem('user_role', 'engineer');
    localStorage.setItem('username', 'eng_user');
    localStorage.setItem('user_id', '5');
    localStorage.setItem('user_full_name', 'Eng User');

    const freshService = new AuthService(
      TestBed.inject(require('@angular/common/http').HttpClient),
      TestBed.inject(require('@angular/router').Router)
    );

    expect(freshService.isAuthenticated()).toBeTrue();
    expect(freshService.getRole()).toBe('engineer');
    expect(freshService.getUsername()).toBe('eng_user');
  });
});
