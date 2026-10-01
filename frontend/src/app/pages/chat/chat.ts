import { Component, ElementRef, ViewChild, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { timeout, catchError } from 'rxjs/operators';
import { TimeoutError, throwError } from 'rxjs';
import { AuthService } from '../../services/auth.service';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  time: string;
  audioBase64?: string;
  logId?: number;
  feedback?: 'up' | 'down';
}

interface ConversationSession {
  id:         string;
  title:      string;
  messages:   { role: 'user' | 'assistant'; content: string; time: string }[];
  startTime:  string;
  msgCount:   number;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.html',
  styleUrl: './chat.scss'
})
export class Chat {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  messages: Message[]  = [];
  userInput            = '';
  isLoading            = false;
  currentTool          = '';
  toolCallCount        = 0;
  isRecording          = false;
  isPlayingAudio       = false;
  isVoiceInput         = false;

  selectedGatewayId:   number | null = null;
  selectedGatewayName: string        = '';

  currentAudio: HTMLAudioElement | null = null;

  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks:   Blob[]               = [];

  private readonly CHAT_VOICE_URL = '/api/chat-voice/';
  private readonly STT_URL        = '/api/voice/stt';
  private readonly TIMEOUT_MS     = 120_000;
  private readonly MAX_STORED     = 50;

  quickActions = [
    { icon: 'pi pi-wifi',       label: 'WiFi Status',     prompt: "What is the WiFi status?" },
    { icon: 'pi pi-desktop',    label: 'Devices',         prompt: "List connected devices" },
    { icon: 'pi pi-globe',      label: 'WAN Status',      prompt: "What is the internet connection status?" },
    { icon: 'pi pi-chart-line', label: 'Speedtest',       prompt: "Run a speedtest" },
    { icon: 'pi pi-shield',     label: 'Firewall',        prompt: "What is the firewall status?" },
    { icon: 'pi pi-key',        label: 'Password',        prompt: "What is the Wi-Fi password?" },
    { icon: 'pi pi-server',     label: 'DHCP',            prompt: "What is the DHCP server status?" },
    { icon: 'pi pi-phone',      label: 'VoIP',            prompt: "What is the VoIP service status?" },
  ];

  private get sessionsKey() {
    const user = this.auth.getUsername() ?? 'guest';
    const gw   = this.selectedGatewayId   ?? 'none';
    return `hgw_sessions_${user}_gw${gw}`;
  }

  conversationSessions: ConversationSession[] = [];
  currentSessionId: string | null = null;

  get reversedSessions(): ConversationSession[] {
    return [...this.conversationSessions].reverse();
  }

  constructor(
    private http: HttpClient,
    private cdr:  ChangeDetectorRef,
    private zone: NgZone,
    private auth: AuthService
  ) {
    this.selectedGatewayId = Number(localStorage.getItem('selected_gateway_id')) || null;
    this.loadSessions();
    this.loadSelectedGateway();
  }

  private loadSelectedGateway() {
    const id = this.selectedGatewayId;
    if (!id) return;
    this.http.get<any>(`/api/gateways/${id}`).subscribe({
      next: (gw) => { this.selectedGatewayName = gw.name || ''; this.cdr.detectChanges(); },
      error: () => {}
    });
  }

  private loadSessions() {
    try {
      const raw = localStorage.getItem(this.sessionsKey);
      this.conversationSessions = raw ? JSON.parse(raw) : [];
    } catch { this.conversationSessions = []; }
  }

  private saveSessions() {
    try {
      localStorage.setItem(this.sessionsKey, JSON.stringify(this.conversationSessions.slice(-20)));
    } catch {}
  }

  private updateCurrentSession() {
    if (!this.currentSessionId) return;
    const idx = this.conversationSessions.findIndex(s => s.id === this.currentSessionId);
    const first = this.messages.find(m => m.role === 'user');
    const entry: ConversationSession = {
      id:        this.currentSessionId,
      title:     first?.content ?? 'Conversation',
      messages:  this.messages.slice(-10).map(m => ({ role: m.role, content: m.content, time: m.time })),
      startTime: idx >= 0 ? this.conversationSessions[idx].startTime : new Date().toISOString(),
      msgCount:  this.messages.length,
    };
    if (idx >= 0) this.conversationSessions[idx] = entry;
    else          this.conversationSessions.push(entry);
    this.saveSessions();
  }

  deleteSession(index: number) {
    const session = this.conversationSessions[index];
    if (session && session.id === this.currentSessionId) {
      this.messages = [];
      this.toolCallCount = 0;
      this.currentSessionId = null;
    }
    this.conversationSessions.splice(index, 1);
    this.saveSessions();
    this.cdr.detectChanges();
  }

  restoreSession(session: ConversationSession) {
    this.messages         = session.messages.map(m => ({ ...m, audioBase64: undefined }));
    this.currentSessionId = session.id;
    this.toolCallCount    = 0;
    this.cdr.detectChanges();
    setTimeout(() => this.scrollToBottom(), 100);
  }

  newConversation() {
    this.messages         = [];
    this.toolCallCount    = 0;
    this.currentSessionId = null;
    this.cdr.detectChanges();
  }

  private saveHistory() {}

  clearHistory() {
    this.messages         = [];
    this.toolCallCount    = 0;
    this.currentSessionId = null;
    this.cdr.detectChanges();
  }

  getTime(): string {
    return new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }

  sendQuickAction(prompt: string) {
    this.userInput = prompt;
    this.sendMessage();
  }

  sendMessage() {
    if (!this.userInput.trim() || this.isLoading) return;

    const userMsg: Message = { role: 'user', content: this.userInput, time: this.getTime() };
    this.messages.push(userMsg);
    const input = this.userInput;
    // Start a new session on the first message of a new conversation
    if (!this.currentSessionId) {
      this.currentSessionId = Date.now().toString();
    }
    this.userInput   = '';
    this.isLoading   = true;
    this.currentTool = 'Connecting to Home Gateway...';
    setTimeout(() => this.scrollToBottom(), 100);

    const gatewayId = Number(localStorage.getItem('selected_gateway_id')) || null;

    this.http.post<{
      response:         string;
      tool_calls_count: number;
      audio_base64?:    string;
      voice_available:  boolean;
      log_id?:          number;
    }>(
      this.CHAT_VOICE_URL,
      {
        message:        input,
        history:        this.messages.slice(-4).map(m => ({ role: m.role, content: m.content })),
        gateway_id:     gatewayId,
        with_voice:     true,
        language_code:  'fr-FR',
        is_voice_input: this.isVoiceInput
      }
    ).pipe(
      timeout(this.TIMEOUT_MS),
      catchError(err => {
        if (err instanceof TimeoutError) return throwError(() => ({ type: 'timeout' }));
        return throwError(() => ({ type: 'http', err }));
      })
    ).subscribe({
      next: (res) => {
        this.zone.run(() => {
          this.toolCallCount += res.tool_calls_count || 0;
          this.isLoading      = false;
          this.currentTool    = '';
          this.isVoiceInput   = false;  // 👈 Reset flag après message
          this.messages.push({
            role:        'assistant',
            content:     res.response,
            time:        this.getTime(),
            audioBase64: res.audio_base64 || undefined,
            logId:       res.log_id,
          });
          this.updateCurrentSession();
          this.cdr.detectChanges();
          setTimeout(() => this.scrollToBottom(), 100);
        });
      },
      error: (e) => {
        this.zone.run(() => {
          this.isLoading   = false;
          this.currentTool = '';
          let text: string;
          if (e?.type === 'timeout') {
            text = '⏱️ Request timed out after 2 minutes.';
          } else {
            const status = (e?.err as HttpErrorResponse)?.status;
            if      (status === 0 || status == null) text = '❌ Unable to reach the backend.';
            else if (status === 422)                 text = '❌ Error 422 — Invalid data.';
            else                                     text = `❌ Error ${status ?? ''} — Unexpected error.`;
          }
          this.messages.push({ role: 'assistant', content: text, time: this.getTime() });
          this.saveHistory();
          this.cdr.detectChanges();
          setTimeout(() => this.scrollToBottom(), 100);
        });
      }
    });
  }

  // ── Play / Stop audio ─────────────────────────────────────────────────────
  playAudio(msg: Message) {
    // Toggle stop if already playing
    if (this.isPlayingAudio && this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio   = null;
      this.isPlayingAudio = false;
      this.cdr.detectChanges();
      return;
    }
    if (!msg.audioBase64) return;

    try {
      const bytes = Uint8Array.from(atob(msg.audioBase64), c => c.charCodeAt(0));
      const blob  = new Blob([bytes], { type: 'audio/mp3' });
      const url   = URL.createObjectURL(blob);

      this.currentAudio   = new Audio(url);
      this.isPlayingAudio = true;
      this.cdr.detectChanges();

      this.currentAudio.onended = () => this.zone.run(() => {
        this.isPlayingAudio = false;
        this.currentAudio   = null;
        URL.revokeObjectURL(url);
        this.cdr.detectChanges();
      });
      this.currentAudio.onerror = () => this.zone.run(() => {
        this.isPlayingAudio = false;
        this.currentAudio   = null;
        this.cdr.detectChanges();
      });

      this.currentAudio.play();
    } catch (err) {
      console.error('[Audio]', err);
      this.isPlayingAudio = false;
    }
  }

  // ── Microphone ────────────────────────────────────────────────────────────
  async startRecording() {
    try {
      this.audioChunks   = [];
      const stream       = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream);

      this.mediaRecorder.ondataavailable = e => { if (e.data.size > 0) this.audioChunks.push(e.data); };
      this.mediaRecorder.onstart        = () => { this.isRecording = true;  this.cdr.detectChanges(); };
      this.mediaRecorder.onstop         = () => { this.isRecording = false; this._processAudio(); };
      this.mediaRecorder.start(250);
    } catch {
      alert('Erreur : microphone non disponible');
    }
  }

  stopRecording() {
    if (this.mediaRecorder && this.isRecording) {
      this.mediaRecorder.stop();
      this.mediaRecorder.stream.getTracks().forEach(t => t.stop());
    }
  }

  private _processAudio() {
    const ext      = this.audioChunks[0]?.type.includes('ogg') ? 'ogg' : 'webm';
    const blob     = new Blob(this.audioChunks, { type: `audio/${ext}` });
    const formData = new FormData();
    formData.append('audio', blob, `recording.${ext}`);

    this.isLoading = true;
    this.cdr.detectChanges();

    this.http.post<{ text: string }>(this.STT_URL, formData).subscribe({
      next: res => this.zone.run(() => {
        this.userInput    = res.text;
        this.isVoiceInput = true;  // 👈 Mark as voice input
        this.isLoading    = false;
        this.cdr.detectChanges();
        if (this.userInput.trim()) this.sendMessage();
      }),
      error: () => this.zone.run(() => {
        alert('Error during audio transcription');
        this.isLoading = false;
        this.cdr.detectChanges();
      })
    });
  }

  scrollToBottom() {
    try {
      const el = this.messagesContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    } catch {}
  }

  truncate(text: string, max = 32): string {
    return text.length > max ? text.slice(0, max) + '…' : text;
  }

  // ── Feedback 👍 / 👎 ─────────────────────────────────────────────────────
  sendFeedback(msg: Message, value: 'up' | 'down') {
    if (!msg.logId || msg.feedback) return;
    msg.feedback = value;
    this.cdr.detectChanges();
    this.http.post(`/api/chat-logs/${msg.logId}/feedback`, { value }).subscribe({
      error: () => { msg.feedback = undefined; this.cdr.detectChanges(); }
    });
  }

  // ── Export conversation ───────────────────────────────────────────────────
  exportJson() {
    const data = {
      exportedAt: new Date().toISOString(),
      gateway:    this.selectedGatewayName || 'unknown',
      user:       this.auth.getUsername(),
      messages:   this.messages.map(m => ({
        role:     m.role,
        content:  m.content,
        time:     m.time,
        feedback: m.feedback ?? null,
      })),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `conversation_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  exportPdf() {
    const lines = this.messages.map(m => {
      const who = m.role === 'user' ? `You (${m.time})` : `Assistant (${m.time})`;
      return `<div class="msg ${m.role}"><strong>${who}</strong><p>${m.content.replace(/\n/g, '<br>')}</p></div>`;
    }).join('');

    const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
    <title>Conversation Export</title>
    <style>
      body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; color: #1e293b; }
      h2   { color: #6366f1; }
      .msg { margin: 16px 0; padding: 12px; border-radius: 8px; }
      .user      { background: #eff6ff; border-left: 4px solid #6366f1; }
      .assistant { background: #f0fdf4; border-left: 4px solid #22c55e; }
      strong { font-size: 0.85em; color: #64748b; }
      p { margin: 6px 0 0; }
    </style></head><body>
    <h2>HGW Conversation — ${this.selectedGatewayName || 'Gateway'}</h2>
    <p style="color:#64748b">Exported ${new Date().toLocaleString()} · User: ${this.auth.getUsername()}</p>
    <hr>${lines}</body></html>`;

    const blob   = new Blob([html], { type: 'text/html' });
    const url    = URL.createObjectURL(blob);
    const w      = window.open(url, '_blank');
    if (!w) return;
    setTimeout(() => { w.print(); URL.revokeObjectURL(url); }, 600);
  }
}