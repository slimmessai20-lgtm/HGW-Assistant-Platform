import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class Dashboard implements OnInit {
  private http   = inject(HttpClient);
  private cdr    = inject(ChangeDetectorRef);
  private router = inject(Router);

  gateways: any[] = [];
  loading  = true;
  pinging  = false;

  // ping results keyed by gateway id
  pingResults = new Map<number, { status: string; latency_ms: number | null }>();

  ngOnInit() {
    this.loadGateways();
  }

  loadGateways() {
    this.loading = true;
    this.http.get<any[]>('/api/gateways').subscribe({
      next: (list) => {
        this.gateways = list;
        this.loading  = false;
        this.cdr.detectChanges();
        this.pingAll();
      },
      error: () => { this.loading = false; this.cdr.detectChanges(); }
    });
  }

  pingAll() {
    this.pinging = true;
    let pending  = this.gateways.length;
    if (pending === 0) { this.pinging = false; return; }

    for (const gw of this.gateways) {
      this.http.get<any>(`/api/gateways/${gw.id}/ping`).subscribe({
        next: (r) => {
          this.pingResults.set(gw.id, r);
          if (--pending === 0) { this.pinging = false; }
          this.cdr.detectChanges();
        },
        error: () => {
          this.pingResults.set(gw.id, { status: 'unreachable', latency_ms: null });
          if (--pending === 0) { this.pinging = false; }
          this.cdr.detectChanges();
        }
      });
    }
  }

  openChat(gw: any) {
    localStorage.setItem('selected_gateway_id', String(gw.id));
    this.router.navigate(['/dashboard/chat']);
  }

  ping(gw: any): { status: string; latency_ms: number | null } {
    return this.pingResults.get(gw.id) ?? { status: 'pending', latency_ms: null };
  }

  pingClass(gw: any): string {
    const s = this.ping(gw).status;
    if (s === 'reachable')   return 'dot-green';
    if (s === 'unreachable' || s === 'timeout') return 'dot-red';
    return 'dot-grey';
  }

  pingLabel(gw: any): string {
    const r = this.ping(gw);
    if (r.status === 'reachable')   return r.latency_ms != null ? `${r.latency_ms} ms` : 'Reachable';
    if (r.status === 'timeout')     return 'Timeout';
    if (r.status === 'unreachable') return 'Unreachable';
    return '…';
  }

  brandColor(brand: string | null): string {
    switch ((brand ?? '').toLowerCase()) {
      case 'kpn':      return '#009de0';
      case 'swisscom': return '#1565c0';
      default:         return '#64748b';
    }
  }

  brandFlag(brand: string | null): string {
    switch ((brand ?? '').toLowerCase()) {
      case 'kpn':      return 'https://flagcdn.com/w20/nl.png';
      case 'swisscom': return 'https://flagcdn.com/w20/ch.png';
      default:         return '';
    }
  }

  get offlineGateways(): any[] {
    return this.gateways.filter(gw => {
      const s = this.pingResults.get(gw.id)?.status;
      return s === 'unreachable' || s === 'timeout';
    });
  }
}
