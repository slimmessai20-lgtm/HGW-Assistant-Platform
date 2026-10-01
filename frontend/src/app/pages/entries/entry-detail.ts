import { Component, OnInit, OnDestroy, ElementRef, ViewChild, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { ChartModule } from 'primeng/chart';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { timeout, catchError } from 'rxjs/operators';
import { TimeoutError, throwError, interval, Subscription } from 'rxjs';

interface Gateway {
  id: number;
  name: string;
  brand: string;
  surname: string;
  mac_address: string;
  ipv4_address: string;
  ipv6_address: string;
  telnet_host: string;
  telnet_port: number;
  telnet_user: string;
  software_version: string;
  serial_number: string;
  base_mac: string;
  status: 'active' | 'inactive' | 'unknown';
  notes: string;
  created_at: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  time: string;
}

@Component({
  selector: 'app-entry-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, TagModule, ButtonModule, TooltipModule, ChartModule, ToastModule],
  providers: [MessageService],
  templateUrl: './entry-detail.html',
  styleUrl: './entry-detail.scss'
})
export class EntryDetail implements OnInit, OnDestroy {
  @ViewChild('chatMessages') chatMessages!: ElementRef;

  gateway: Gateway | null = null;
  loading = true;
  gatewayId!: number;

  // Ping chart
  pingData: any;
  pingOptions: any;
  pingHistory: number[] = [];
  pingLabels: string[] = [];
  pingStatus: 'reachable' | 'timeout' | 'unreachable' | 'unknown' = 'unknown';
  pingLatency: number | null = null;
  private pingInterval$?: Subscription;

  // Fetch KPIs
  fetchLoading = false;

  // Chat
  messages: ChatMessage[] = [];
  userInput = '';
  chatLoading = false;
  currentTool = '';

  quickActions = [
    { icon: 'pi pi-wifi',        label: 'Wi-Fi',     prompt: 'What is the Wi-Fi status?' },
    { icon: 'pi pi-desktop',     label: 'Devices',   prompt: 'List connected devices' },
    { icon: 'pi pi-globe',       label: 'WAN',       prompt: 'What is the internet connection status?' },
    { icon: 'pi pi-server',      label: 'DHCP',      prompt: 'What is the DHCP server status?' },
    { icon: 'pi pi-shield',      label: 'Firewall',  prompt: 'What is the firewall status?' },
    { icon: 'pi pi-chart-line',  label: 'Throughput', prompt: 'Show network throughput statistics' },
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private zone: NgZone,
    private toast: MessageService
  ) {}

  ngOnInit() {
    this.gatewayId = +this.route.snapshot.paramMap.get('id')!;
    this.loadGateway();
    this.initPingChart();
  }

  ngOnDestroy() {
    this.pingInterval$?.unsubscribe();
  }

  loadGateway() {
    this.loading = true;
    this.http.get<Gateway>(`/api/gateways/${this.gatewayId}`).subscribe({
      next: gw => {
        this.zone.run(() => {
          this.gateway = gw;
          this.loading = false;
          this.cdr.detectChanges();
          this.startPingPolling();
        });
      },
      error: () => {
        this.zone.run(() => {
          this.loading = false;
          this.router.navigate(['/dashboard/entries']);
        });
      }
    });
  }

  // ── Ping ──────────────────────────────────────────
  initPingChart() {
    this.pingData = {
      labels: [],
      datasets: [{
        label: 'Latence (ms)',
        data: [],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#3b82f6',
      }]
    };
    this.pingOptions = {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { display: false },
        y: {
          min: 0,
          ticks: { color: '#94a3b8' },
          grid: { color: 'rgba(148,163,184,0.1)' }
        }
      }
    };
  }

  startPingPolling() {
    this.doPing();
    this.pingInterval$ = interval(8000).subscribe(() => this.doPing());
  }

  doPing() {
    this.http.get<any>(`/api/gateways/${this.gatewayId}/ping`).subscribe({
      next: res => {
        this.zone.run(() => {
          this.pingStatus = res.status;
          this.pingLatency = res.latency_ms;
          const now = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
          if (res.latency_ms !== null) {
            this.pingHistory.push(res.latency_ms);
            this.pingLabels.push(now);
            if (this.pingHistory.length > 20) {
              this.pingHistory.shift();
              this.pingLabels.shift();
            }
            this.pingData = {
              ...this.pingData,
              labels: [...this.pingLabels],
              datasets: [{ ...this.pingData.datasets[0], data: [...this.pingHistory] }]
            };
          }
          this.cdr.detectChanges();
        });
      }
    });
  }

  get pingStatusLabel(): string {
    switch (this.pingStatus) {
      case 'reachable':   return 'Online';
      case 'timeout':     return 'Timeout';
      case 'unreachable': return 'Offline';
      default:            return 'Unknown';
    }
  }

  get pingStatusSeverity(): 'success' | 'warn' | 'danger' | 'secondary' {
    switch (this.pingStatus) {
      case 'reachable':   return 'success';
      case 'timeout':     return 'warn';
      case 'unreachable': return 'danger';
      default:            return 'secondary';
    }
  }

  // ── Chat ──────────────────────────────────────────
  getTime(): string {
    return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }

  sendQuickAction(prompt: string) {
    this.userInput = prompt;
    this.sendMessage();
  }

  sendMessage() {
    if (!this.userInput.trim() || this.chatLoading) return;
    const msg: ChatMessage = { role: 'user', content: this.userInput, time: this.getTime() };
    this.messages.push(msg);
    const input = this.userInput;
    this.userInput = '';
    this.chatLoading = true;
    this.currentTool = `Connecting to ${this.gateway?.name ?? 'HGW'}...`;
    setTimeout(() => this.scrollChat(), 80);

    this.http.post<{ response: string; tool_calls_count: number }>('/api/chat', {
      message: input,
      gateway_id: this.gatewayId,
      history: this.messages.slice(-4).map(m => ({ role: m.role, content: m.content }))
    }).pipe(
      timeout(120_000),
      catchError(err => {
        if (err instanceof TimeoutError) return throwError(() => ({ type: 'timeout' }));
        return throwError(() => ({ type: 'http', err }));
      })
    ).subscribe({
      next: res => {
        this.zone.run(() => {
          this.chatLoading = false;
          this.currentTool = '';
          this.messages.push({ role: 'assistant', content: res.response, time: this.getTime() });
          this.cdr.detectChanges();
          setTimeout(() => this.scrollChat(), 80);
        });
      },
      error: e => {
        this.zone.run(() => {
          this.chatLoading = false;
          this.currentTool = '';
          const msg = e?.type === 'timeout' ? 'Timeout: the HGW is not responding.' : 'Connection error.';
          this.messages.push({ role: 'assistant', content: msg, time: this.getTime() });
          this.cdr.detectChanges();
        });
      }
    });
  }

  scrollChat() {
    if (this.chatMessages?.nativeElement) {
      const el = this.chatMessages.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }

  getStatusSeverity(status: string): 'success' | 'warn' | 'danger' | 'secondary' {
    return status === 'active' ? 'success' : status === 'inactive' ? 'danger' : 'secondary';
  }

  getStatusLabel(status: string): string {
    return status === 'active' ? 'Active' : status === 'inactive' ? 'Inactive' : 'Unknown';
  }

  getBrandIcon(brand: string): string {
    const icons: Record<string, string> = {
      'KPN': 'pi pi-building',
      'Swisscom': 'pi pi-globe',
      'Orange': 'pi pi-wifi',
      'SFR': 'pi pi-bolt',
      'Bouygues': 'pi pi-signal',
      'Proximus': 'pi pi-star',
    };
    return icons[brand] ?? 'pi pi-server';
  }

  /** Appelle le backend → Telnet HGW → récupère SerialNumber + BaseMAC + etc. → met à jour la vue */
  fetchDeviceInfo() {
    this.fetchLoading = true;
    this.http.post<{ serial_number: string; base_mac: string; software_version: string; ipv4_address: string; ipv6_address: string; mac_address: string; message: string }>(
      `/api/gateways/${this.gatewayId}/fetch-device-info`, {}
    ).subscribe({
      next: res => {
        this.zone.run(() => {
          if (this.gateway) {
            if (res.serial_number) this.gateway.serial_number = res.serial_number;
            if (res.base_mac)      this.gateway.base_mac      = res.base_mac;
            if (res.software_version) this.gateway.software_version = res.software_version;
            if (res.ipv4_address)  this.gateway.ipv4_address  = res.ipv4_address;
            if (res.ipv6_address)  this.gateway.ipv6_address  = res.ipv6_address;
            if (res.mac_address)   this.gateway.mac_address   = res.mac_address;
          }
          this.fetchLoading = false;
          this.toast.add({
            severity: 'success',
            summary: 'KPIs récupérés !',
            detail: `Serial, Base MAC, IP, et Version mis à jour depuis le HGW`,
            life: 5000
          });
          this.cdr.detectChanges();
        });
      },
      error: (e) => {
        this.zone.run(() => {
          this.fetchLoading = false;
          this.toast.add({
            severity: 'error',
            summary: 'Erreur',
            detail: e.error?.detail ?? 'Connexion Telnet impossible',
            life: 5000
          });
          this.cdr.detectChanges();
        });
      }
    });
  }
}

