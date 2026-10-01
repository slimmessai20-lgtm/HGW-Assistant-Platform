import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-admin-requests',
  standalone: true,
  imports: [CommonModule, TableModule, ButtonModule, ToastModule],
  providers: [MessageService],
  templateUrl: './admin-requests.html',
  styleUrl: './admin-requests.scss'
})
export class AdminRequests implements OnInit {
  requests: any[] = [];
  isLoading = false;
  processingId: number | null = null;

  constructor(private http: HttpClient, private toast: MessageService) {}

  ngOnInit() {
    this.loadRequests();
  }

  loadRequests() {
    this.isLoading = true;
    this.http.get<any[]>('/api/auth/requests').subscribe({
      next: (data) => {
        this.requests = data;
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
        this.toast.add({ severity: 'error', summary: 'Error', detail: 'Could not load requests' });
      }
    });
  }

  approveRequest(req: any) {
    this.processingId = req.id;
    this.http.post<{message: string}>(`/api/auth/requests/${req.id}/approve`, {}).subscribe({
      next: (res) => {
        this.processingId = null;
        this.toast.add({ severity: 'success', summary: 'Approved', detail: res.message });
        this.loadRequests();
      },
      error: (err) => {
        this.processingId = null;
        this.toast.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to approve' });
      }
    });
  }

  rejectRequest(req: any) {
    this.processingId = req.id;
    this.http.post<{message: string}>(`/api/auth/requests/${req.id}/reject`, {}).subscribe({
      next: (res) => {
        this.processingId = null;
        this.toast.add({ severity: 'success', summary: 'Rejected', detail: res.message });
        this.loadRequests();
      },
      error: (err) => {
        this.processingId = null;
        this.toast.add({ severity: 'error', summary: 'Error', detail: err.error?.detail || 'Failed to reject' });
      }
    });
  }
}
