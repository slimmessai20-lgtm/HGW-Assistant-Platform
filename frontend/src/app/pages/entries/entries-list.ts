import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService, MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { AuthService } from '../../services/auth.service';

interface Gateway {
  id: number;
  name: string;
  brand: string;
  surname: string;
  mac_address: string;
  ipv4_address: string;
  ipv6_address: string;
  software_version: string;
  serial_number: string;
  base_mac: string;
  status: 'active' | 'inactive' | 'unknown';
  notes: string;
  created_at: string;
}

@Component({
  selector: 'app-entries-list',
  standalone: true,
  imports: [
    CommonModule, RouterModule, FormsModule,
    TableModule, ButtonModule, InputTextModule,
    TagModule, TooltipModule, ConfirmDialogModule, ToastModule
  ],
  providers: [ConfirmationService, MessageService],
  templateUrl: './entries-list.html',
  styleUrl: './entries-list.scss'
})
export class EntriesList implements OnInit {
  gateways: Gateway[] = [];
  loading = true;
  searchValue = '';

  constructor(
    private http: HttpClient,
    public auth: AuthService,
    private confirm: ConfirmationService,
    private toast: MessageService,
    private zone: NgZone,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() { this.load(); }

  load() {
    this.loading = true;
    this.http.get<Gateway[]>('/api/gateways').subscribe({
      next: data => this.zone.run(() => {
        this.gateways = data;
        this.loading  = false;
        this.cdr.detectChanges();
      }),
      error: () => this.zone.run(() => {
        this.loading = false;
        this.cdr.detectChanges();
      })
    });
  }

  statusSeverity(s: string): 'success' | 'danger' | 'warn' | 'secondary' {
    return s === 'active' ? 'success' : s === 'inactive' ? 'danger' : 'warn';
  }

  statusLabel(s: string) {
    return s === 'active' ? 'Active' : s === 'inactive' ? 'Inactive' : 'Unknown';
  }

  confirmDelete(gw: Gateway) {
    this.confirm.confirm({
      message: `Delete entry "${gw.name}"?`,
      header: 'Confirmation',
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Delete',
      rejectLabel: 'Cancel',
      acceptButtonStyleClass: 'p-button-danger',
      accept: () => {
        this.http.delete(`/api/gateways/${gw.id}`).subscribe({
          next: () => {
            this.gateways = this.gateways.filter(g => g.id !== gw.id);
            this.toast.add({ severity: 'success', summary: 'Deleted', detail: gw.name, life: 3000 });
          },
          error: (e) => this.toast.add({ severity: 'error', summary: 'Error', detail: e.error?.detail })
        });
      }
    });
  }
}
