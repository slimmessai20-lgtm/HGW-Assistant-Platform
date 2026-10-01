import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface ChatLog {
  id:           number;
  user_id:      number | null;
  username:     string | null;
  gateway_id:   number | null;
  gateway_name: string | null;
  message:      string;
  response:     string;
  tool_calls:   number;
  voice_used:   number;
  duration_ms:  number | null;
  session_id:   number | null;
  user_type:    'general' | 'engineer' | 'admin' | null;
  created_at:   string;
}

@Component({
  selector: 'app-admin-conversations',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-conversations.html',
  styleUrl:    './admin-conversations.scss'
})
export class AdminConversations implements OnInit {

  logs:       ChatLog[] = [];
  loadingLogs = false;

  // ── Pagination ─────────────────────────────────────────────────────────────
  readonly pageSize = 20;
  currentPage = 1;

  get pagedLogs(): ChatLog[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.logs.slice(start, start + this.pageSize);
  }

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.logs.length / this.pageSize));
  }

  get pageNumbers(): (number | '...')[] {
    const total = this.totalPages;
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    const pages: (number | '...')[] = [1];
    if (this.currentPage > 3) pages.push('...');
    const from = Math.max(2, this.currentPage - 1);
    const to   = Math.min(total - 1, this.currentPage + 1);
    for (let i = from; i <= to; i++) pages.push(i);
    if (this.currentPage < total - 2) pages.push('...');
    pages.push(total);
    return pages;
  }

  goToPage(page: number) {
    this.currentPage = Math.max(1, Math.min(page, this.totalPages));
    this.selectedLog = null;
    this.cdr.detectChanges();
  }

  // ── Filters ────────────────────────────────────────────────────────────────
  filterUsername = '';
  filterGateway  = '';
  filterDateFrom = '';
  filterDateTo   = '';
  filterRole     = '';

  // ── Detail panel ──────────────────────────────────────────────────────────
  selectedLog: ChatLog | null = null;

  // ── G/T comparison ─────────────────────────────────────────────────────────
  compareLoading = false;
  compareResult: { general: string; technical: string; general_tools: number; technical_tools: number } | null = null;
  compareError: string | null = null;

  // ── Admin correction ───────────────────────────────────────────────────────
  editedResponse    = '';
  correctionSaved   = false;
  correctionLoading = false;
  existingCorrection: string | null = null;

  constructor(
    private http: HttpClient,
    private zone: NgZone,
    private cdr:  ChangeDetectorRef
  ) {}

  ngOnInit() {
    this.loadLogs();
  }

  loadLogs() {
    this.loadingLogs = true;
    this.currentPage = 1;
    let url = '/api/chat-logs?limit=1000';
    if (this.filterDateFrom) url += `&date_from=${this.filterDateFrom}`;
    if (this.filterDateTo)   url += `&date_to=${this.filterDateTo}`;

    this.http.get<ChatLog[]>(url).subscribe({
      next: data => this.zone.run(() => {
        this.logs = data.filter(l => {
          const u = this.filterUsername.toLowerCase();
          const g = this.filterGateway.toLowerCase();
          return (!u || (l.username    ?? '').toLowerCase().includes(u))
              && (!g || (l.gateway_name ?? '').toLowerCase().includes(g))
              && (!this.filterRole || l.user_type === this.filterRole);
        });
        this.loadingLogs = false;
        this.cdr.detectChanges();
      }),
      error: () => this.zone.run(() => {
        this.loadingLogs = false;
        this.cdr.detectChanges();
      })
    });
  }

  applyFilters() { this.loadLogs(); }

  resetFilters() {
    this.filterUsername = '';
    this.filterGateway  = '';
    this.filterDateFrom = '';
    this.filterDateTo   = '';
    this.filterRole     = '';
    this.loadLogs();
  }

  exportCsv() {
    if (!this.logs.length) return;
    const headers = ['ID', 'User', 'Role', 'Gateway', 'Message', 'Response', 'Tools', 'Voice', 'Duration (ms)', 'Date'];
    const rows = this.logs.map(l => [
      l.id,
      l.username ?? '',
      l.user_type ?? '',
      l.gateway_name ?? '',
      `"${(l.message  ?? '').replace(/"/g, '""')}"`,
      `"${(l.response ?? '').replace(/"/g, '""')}"`,
      l.tool_calls,
      l.voice_used ? 'Yes' : 'No',
      l.duration_ms ?? '',
      l.created_at
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `logs_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  selectLog(log: ChatLog) {
    this.selectedLog      = this.selectedLog?.id === log.id ? null : log;
    this.compareResult    = null;
    this.compareError     = null;
    this.editedResponse   = log.response ?? '';
    this.correctionSaved  = false;
    this.existingCorrection = null;
    if (this.selectedLog) this.loadCorrection(log.id);
  }

  loadCorrection(logId: number) {
    this.http.get<any>(`/api/chat-logs/${logId}/correction`).subscribe({
      next: data => this.zone.run(() => {
        this.existingCorrection = data.corrected_response;
        this.editedResponse     = data.corrected_response;
        this.cdr.detectChanges();
      }),
      error: () => {}
    });
  }

  saveCorrection() {
    if (!this.selectedLog || !this.editedResponse.trim()) return;
    this.correctionLoading = true;
    this.correctionSaved   = false;
    this.http.post(`/api/chat-logs/${this.selectedLog.id}/correct`, {
      corrected_response: this.editedResponse
    }).subscribe({
      next: () => this.zone.run(() => {
        this.correctionSaved    = true;
        this.correctionLoading  = false;
        this.existingCorrection = this.editedResponse;
        this.cdr.detectChanges();
        setTimeout(() => { this.correctionSaved = false; this.cdr.detectChanges(); }, 3000);
      }),
      error: () => this.zone.run(() => {
        this.correctionLoading = false;
        this.cdr.detectChanges();
        alert('Error saving correction.');
      })
    });
  }

  runCompare() {
    if (!this.selectedLog) return;
    this.compareLoading = true;
    this.compareResult  = null;
    this.compareError   = null;
    this.http.post<any>('/api/chat-logs/compare', {
      message:    this.selectedLog.message,
      gateway_id: this.selectedLog.gateway_id
    }).subscribe({
      next: data => this.zone.run(() => {
        this.compareResult  = data;
        this.compareLoading = false;
        this.cdr.detectChanges();
      }),
      error: () => this.zone.run(() => {
        this.compareError   = 'Comparison error. Check that the gateway is reachable.';
        this.compareLoading = false;
        this.cdr.detectChanges();
      })
    });
  }

  deleteLog(log: ChatLog, event: Event) {
    event.stopPropagation();
    if (!confirm(`Delete log #${log.id}?`)) return;
    this.http.delete(`/api/chat-logs/${log.id}`).subscribe({
      next: () => this.zone.run(() => {
        this.logs = this.logs.filter(l => l.id !== log.id);
        if (this.selectedLog?.id === log.id) this.selectedLog = null;
        if (this.currentPage > this.totalPages) this.currentPage = this.totalPages;
        this.cdr.detectChanges();
      }),
      error: () => alert('Error deleting log')
    });
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  formatDate(iso: string): string {
    return new Date(iso).toLocaleString('fr-FR', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  }

  formatDuration(ms: number | null): string {
    if (!ms) return '—';
    return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
  }

  truncate(text: string, max = 75): string {
    return text.length > max ? text.slice(0, max) + '…' : text;
  }

  roleLabel(type: string | null): string {
    return ({ admin: 'Admin', engineer: 'Engineer', general: 'General' } as any)[type ?? ''] ?? '—';
  }

  roleClass(type: string | null): string {
    return ({ admin: 'role-admin', engineer: 'role-engineer', general: 'role-general' } as any)[type ?? ''] ?? '';
  }

  roleIcon(type: string | null): string {
    return ({ admin: 'pi-shield', engineer: 'pi-wrench', general: 'pi-user' } as any)[type ?? ''] ?? 'pi-user';
  }
}
