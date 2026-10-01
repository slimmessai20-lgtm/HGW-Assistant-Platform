import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { SelectModule } from 'primeng/select';
import { TextareaModule } from 'primeng/textarea';
import { ToastModule } from 'primeng/toast';
import { InputNumberModule } from 'primeng/inputnumber';
import { MessageService } from 'primeng/api';
import { debounceTime, Subject } from 'rxjs';

@Component({
  selector: 'app-entries-add',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule,
    InputTextModule, ButtonModule, SelectModule, TextareaModule,
    ToastModule, InputNumberModule],
  providers: [MessageService],
  templateUrl: './entries-add.html',
  styleUrl: './entries-add.scss'
})
export class EntriesAdd implements OnInit {
  isLoading = false;
  surnameLoading = false;
  isEditMode = false;
  editId: number | null = null;
  private ipv4Change$ = new Subject<string>();

  form = {
    name: '',
    brand: '',
    surname: '',
    mac_address: '',
    ipv4_address: '',
    ipv6_address: '',
    telnet_host: '',
    telnet_port: 23,
    telnet_user: 'admin',
    telnet_password: '',
    software_version: '',
    serial_number: '',
    base_mac: '',
    status: 'unknown',
    notes: ''
  };

  brandOptions = [
    { label: 'KPN',      value: 'KPN' },
    { label: 'Swisscom', value: 'Swisscom' },
    { label: 'Other',    value: 'Other' }
  ];

  private readonly brandDefaults: Record<string, { user: string; password: string; port: number }> = {
    KPN:      { user: 'root', password: 'sah', port: 23 },
    Swisscom: { user: 'root', password: 'sah', port: 23 },
  };

  statusOptions = [
    { label: 'Active',   value: 'active' },
    { label: 'Inactive', value: 'inactive' },
    { label: 'Unknown',  value: 'unknown' }
  ];

  constructor(private http: HttpClient, private router: Router,
              private route: ActivatedRoute,
              private toast: MessageService) {
    this.ipv4Change$.pipe(debounceTime(600)).subscribe(ip => {
      if (ip && this.isValidIPv4(ip) && !this.isEditMode) this.resolveSurname(ip);
    });
  }

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.isEditMode = true;
      this.editId = parseInt(id, 10);
      this.loadGateway();
    }
  }

  loadGateway() {
    this.isLoading = true;
    this.http.get<any>(`/api/gateways/${this.editId}`).subscribe({
      next: (gw) => {
        // Populate form with existing data
        this.form = { ...this.form, ...gw };
        this.isLoading = false;
      },
      error: () => {
        this.isLoading = false;
        this.toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load gateway' });
        this.router.navigate(['/dashboard/entries']);
      }
    });
  }

  isValidIPv4(ip: string): boolean {
    return /^(\d{1,3}\.){3}\d{1,3}$/.test(ip);
  }

  onBrandChange() {
    const defaults = this.brandDefaults[this.form.brand];
    if (defaults) {
      this.form.telnet_user     = defaults.user;
      this.form.telnet_password = defaults.password;
      this.form.telnet_port     = defaults.port;
    }
  }

  onIpv4Change() {
    if (!this.form.telnet_host) {
      this.form.telnet_host = this.form.ipv4_address;
    }
    this.ipv4Change$.next(this.form.ipv4_address);
  }

  resolveSurname(ip: string) {
    this.surnameLoading = true;
    this.http.get<{ surname: string }>(`/api/gateways/resolve-surname?ipv4=${ip}`).subscribe({
      next: (r) => {
        this.form.surname = r.surname;
        this.surnameLoading = false;
      },
      error: () => {
        this.form.surname = `HGW-${ip.replace(/\./g, '-')}`;
        this.surnameLoading = false;
      }
    });
  }

  formatMac() {
    const v = this.form.mac_address.replace(/[^a-fA-F0-9]/g, '').toUpperCase();
    this.form.mac_address = (v.match(/.{1,2}/g) ?? []).join(':').slice(0, 17);
  }

  submit() {
    if (!this.form.name) return;
    this.isLoading = true;
    
    if (this.isEditMode) {
      this.http.put(`/api/gateways/${this.editId}`, this.form).subscribe({
        next: () => {
          this.toast.add({ severity: 'success', summary: 'Entry updated!', life: 2000 });
          setTimeout(() => this.router.navigate(['/dashboard/entries']), 1500);
        },
        error: (e) => {
          this.isLoading = false;
          this.toast.add({ severity: 'error', summary: 'Error',
            detail: e.error?.detail ?? 'Server error' });
        }
      });
    } else {
      this.http.post('/api/gateways', this.form).subscribe({
        next: () => {
          this.toast.add({ severity: 'success', summary: 'Entry created!', life: 2000 });
          setTimeout(() => this.router.navigate(['/dashboard/entries']), 1500);
        },
        error: (e) => {
          this.isLoading = false;
          this.toast.add({ severity: 'error', summary: 'Error',
            detail: e.error?.detail ?? 'Server error' });
        }
      });
    }
  }
}
