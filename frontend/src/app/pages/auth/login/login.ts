import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { DialogModule } from 'primeng/dialog';
import { AuthService } from '../../../services/auth.service';
import { HttpClient } from '@angular/common/http';
import { SelectModule } from 'primeng/select';

import { TextareaModule } from 'primeng/textarea';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, InputTextModule, PasswordModule, ButtonModule, MessageModule, DialogModule, TextareaModule, SelectModule],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login {
  username = '';
  password = '';
  isLoading = false;
  errorMsg  = '';

  showForgotModal = false;
  forgotEmail = '';
  forgotLoading = false;
  forgotMsg = '';

  showRequestModal = false;
  reqFirstName = '';
  reqLastName = '';
  reqEmail = '';
  reqMessage = '';
  reqRole = 'general';
  reqLoading = false;
  requestMsg = '';

  roleOptions = [
    { label: 'General User', value: 'general' },
    { label: 'Engineer', value: 'engineer' },
    { label: 'Administrator', value: 'admin' }
  ];

  constructor(private router: Router, private authService: AuthService, private http: HttpClient, private cdr: ChangeDetectorRef) {}

  login() {
    if (!this.username || !this.password) return;
    this.isLoading = true;
    this.errorMsg  = '';

    this.authService.login(this.username, this.password).subscribe({
      next: () => {
        this.isLoading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.isLoading = false;
        
        // Log the exact error to the UI for debugging if it's strange
        const defaultMsg = 'Login failed. Please check your credentials.';
        try {
          this.errorMsg = err.error?.detail ?? err.error?.error ?? defaultMsg;
        } catch(e) {
          this.errorMsg = defaultMsg;
        }

        this.cdr.detectChanges(); // Force UI update
      }
    });
  }

  requestPasswordReset() {
    if (!this.forgotEmail) return;
    this.forgotLoading = true;
    this.forgotMsg = '';

    this.http.post<{message: string}>('/api/auth/forgot-password', { email: this.forgotEmail }).subscribe({
      next: (res) => {
        this.forgotLoading = false;
        this.forgotMsg = res.message;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.forgotLoading = false;
        this.forgotMsg = err.error?.detail || err.error?.error || 'Error processing request.';
        this.cdr.detectChanges();
      }
    });
  }

  submitAccountRequest() {
    if (!this.reqFirstName || !this.reqLastName || !this.reqEmail) return;
    this.reqLoading = true;
    this.requestMsg = '';

    const body = {
      first_name: this.reqFirstName,
      last_name: this.reqLastName,
      email: this.reqEmail,
      message: this.reqMessage,
      role: this.reqRole
    };

    this.http.post<{message: string}>('/api/auth/request-account', body).subscribe({
      next: (res) => {
        this.reqLoading = false;
        this.requestMsg = res.message;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.reqLoading = false;
        this.requestMsg = err.error?.detail || err.error?.error || 'Error submitting request.';
        this.cdr.detectChanges();
      }
    });
  }
}