import { Component, OnInit, NgZone, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface PromptSection {
  system?: string;
  max_tokens?: number;
}

interface PromptsConfig {
  general:          PromptSection;
  technical:        PromptSection;
  context_commands: PromptSection;
}

@Component({
  selector:    'app-admin-prompts',
  standalone:  true,
  imports:     [CommonModule, FormsModule],
  templateUrl: './admin-prompts.html',
  styleUrl:    './admin-prompts.scss'
})
export class AdminPrompts implements OnInit {

  config: PromptsConfig | null = null;
  loading  = true;
  saving   = false;
  reloading = false;
  saved    = false;
  error    = '';

  constructor(
    private http: HttpClient,
    private zone: NgZone,
    private cdr:  ChangeDetectorRef
  ) {}

  ngOnInit() { this.loadPrompts(); }

  loadPrompts() {
    this.loading = true;
    this.error   = '';
    this.http.get<PromptsConfig>('/api/prompts').subscribe({
      next: data => this.zone.run(() => {
        this.config  = data;
        this.loading = false;
        this.cdr.detectChanges();
      }),
      error: () => this.zone.run(() => {
        this.error   = 'Failed to load prompts configuration.';
        this.loading = false;
        this.cdr.detectChanges();
      })
    });
  }

  save() {
    if (!this.config) return;
    this.saving = true;
    this.saved  = false;
    this.error  = '';

    this.http.put('/api/prompts', this.config).subscribe({
      next: () => this.zone.run(() => {
        this.saving = false;
        this.saved  = true;
        this.cdr.detectChanges();
        setTimeout(() => { this.saved = false; this.cdr.detectChanges(); }, 3000);
      }),
      error: (err) => this.zone.run(() => {
        this.saving = false;
        this.error  = err?.error?.detail || 'Failed to save prompts.';
        this.cdr.detectChanges();
      })
    });
  }

  reload() {
    this.reloading = true;
    this.error     = '';
    this.http.post('/api/prompts/reload', {}).subscribe({
      next: (res: any) => this.zone.run(() => {
        this.config    = res.config;
        this.reloading = false;
        this.cdr.detectChanges();
      }),
      error: () => this.zone.run(() => {
        this.error     = 'Failed to reload prompts from disk.';
        this.reloading = false;
        this.cdr.detectChanges();
      })
    });
  }
}
