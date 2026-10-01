import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute, RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, PasswordModule, ButtonModule],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.scss'
})
export class ResetPassword implements OnInit {
  token = '';
  newPassword = '';
  confirmPassword = '';
  isLoading = false;
  errorMsg = '';
  successMsg = '';

  constructor(private router: Router, private route: ActivatedRoute, private http: HttpClient) {}

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.token = params['token'] || '';
      if (!this.token) {
        this.errorMsg = 'Invalid or missing reset token. Please request a new link.';
      }
    });
  }

  resetPassword() {
    if (!this.token || !this.newPassword || !this.confirmPassword) return;

    if (this.newPassword !== this.confirmPassword) {
      this.errorMsg = 'Passwords do not match.';
      return;
    }
    
    if (this.newPassword.length < 8) {
        this.errorMsg = 'Password must be at least 8 characters long.';
        return;
    }

    this.isLoading = true;
    this.errorMsg = '';
    this.successMsg = '';

    this.http.post<{message: string}>('/api/auth/reset-password', {
      token: this.token,
      new_password: this.newPassword
    }).subscribe({
      next: (res) => {
        this.isLoading = false;
        this.successMsg = res.message;
        setTimeout(() => this.router.navigate(['/auth/login']), 3000);
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMsg = err.error?.detail ?? 'An error occurred while resetting the password.';
      }
    });
  }
}
