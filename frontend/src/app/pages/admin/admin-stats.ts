import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { ChartModule } from 'primeng/chart';
import { interval, Subscription, forkJoin } from 'rxjs';

@Component({
  selector: 'app-admin-stats',
  standalone: true,
  imports: [CommonModule, ChartModule],
  templateUrl: './admin-stats.html',
  styleUrl: './admin-stats.scss'
})
export class AdminStats implements OnInit, OnDestroy {
  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);
  private refreshSubscription?: Subscription;

  // ── KPI Cards ────────────────────────────────────────────────────────────
  kpi = {
    total_messages: 0,
    voice_messages: 0,
    text_messages: 0,
    active_users_24h: 0,
    gateways_count: 0,
    voice_percentage: 0
  };

  // ── Charts ───────────────────────────────────────────────────────────────
  activityChartData: any = { labels: [], datasets: [] };
  activityChartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#94a3b8', font: { size: 11 } } } },
    scales: {
      x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: { beginAtZero: true, ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } }
    }
  };
  voiceTextChartData: any = { labels: ['Text', 'Voice'], datasets: [{ data: [0, 0], backgroundColor: ['#3b82f6', '#8b5cf6'], borderWidth: 0 }] };
  voiceTextChartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 16, font: { size: 12 } } } }
  };

  // ── Tables ───────────────────────────────────────────────────────────────
  topUsers: any[] = [];
  recentMessages: any[] = [];

  // ── New analytics ─────────────────────────────────────────────────────────
  topQuestions:  any[]  = [];
  feedbackStats: any    = { up_count: 0, down_count: 0, total_rated: 0, positive_rate: 0, rated_rate: 0 };
  responseTime:  any    = { overall: null, by_type: [] };
  hourlyChartData:    any = { labels: [], datasets: [] };
  hourlyChartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
      y: { beginAtZero: true, ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.04)' } }
    }
  };

  // ── Auto-refresh ─────────────────────────────────────────────────────────
  isRefreshing = false;
  lastUpdate = new Date();

  ngOnInit() {
    this.loadAllStats();

    this.refreshSubscription = interval(30000).subscribe(() => {
      this.loadAllStats();
    });
  }

  ngOnDestroy() {
    this.refreshSubscription?.unsubscribe();
  }

  // ── Load All Stats ───────────────────────────────────────────────────────
  loadAllStats() {
    this.isRefreshing = true;
    this.lastUpdate = new Date();

    forkJoin([
      this.http.get<any>('/api/admin/stats/kpi'),
      this.http.get<any>('/api/admin/stats/activity'),
      this.http.get<any>('/api/admin/stats/voice-text'),
      this.http.get<any[]>('/api/admin/stats/top-users?limit=5'),
      this.http.get<any[]>('/api/admin/stats/recent-messages?limit=20'),
      this.http.get<any[]>('/api/admin/stats/top-questions?limit=10'),
      this.http.get<any>('/api/admin/stats/feedback'),
      this.http.get<any>('/api/admin/stats/response-time'),
      this.http.get<any>('/api/admin/stats/hourly'),
    ]).subscribe({
      next: ([kpi, activity, voiceText, topUsers, recentMessages, topQuestions, feedback, responseTime, hourly]) => {
        this.kpi = kpi;

        const dates = Object.keys(activity).sort();
        this.activityChartData = {
          labels: dates,
          datasets: [
            { label: 'Total Messages', data: dates.map(d => activity[d].count), backgroundColor: '#3b82f6', borderColor: '#1e40af', borderWidth: 1 },
            { label: 'Voice Messages', data: dates.map(d => activity[d].voice), backgroundColor: '#8b5cf6', borderColor: '#6d28d9', borderWidth: 1 }
          ]
        };

        this.topUsers       = topUsers;
        this.recentMessages = recentMessages;
        this.topQuestions   = topQuestions;
        this.feedbackStats  = feedback;
        this.responseTime   = responseTime;

        // Hourly heatmap chart
        const hours = Array.from({ length: 24 }, (_, i) => `${i}h`);
        this.hourlyChartData = {
          labels: hours,
          datasets: [{
            label: 'Messages',
            data: Array.from({ length: 24 }, (_, i) => hourly[i] ?? 0),
            backgroundColor: Array.from({ length: 24 }, (_, i) => {
              const val = hourly[i] ?? 0;
              const max = Math.max(...Object.values(hourly) as number[], 1);
              const alpha = 0.2 + (val / max) * 0.8;
              return `rgba(99,102,241,${alpha.toFixed(2)})`;
            }),
            borderRadius: 4,
          }]
        };

        this.isRefreshing = false;
        this.cdr.detectChanges();

        setTimeout(() => {
          this.voiceTextChartData = {
            labels: ['Text', 'Voice'],
            datasets: [{ data: [voiceText.text, voiceText.voice], backgroundColor: ['#3b82f6', '#8b5cf6'], hoverBackgroundColor: ['#1e40af', '#6d28d9'] }]
          };
          this.cdr.detectChanges();
        }, 100);
      },
      error: (err) => {
        console.error('❌ Stats load error:', err);
        this.isRefreshing = false;
        this.cdr.detectChanges();
      }
    });
  }

  // ── Refresh Manual ───────────────────────────────────────────────────────
  manualRefresh() {
    this.loadAllStats();
  }

  // ── Format Duration ─────────────────────────────────────────────────────
  formatDuration(ms: number): string {
    if (!ms) return '—';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  }

  feedbackBar(count: number): number {
    const total = this.feedbackStats.up_count + this.feedbackStats.down_count;
    return total > 0 ? Math.round((count / total) * 100) : 0;
  }
}


