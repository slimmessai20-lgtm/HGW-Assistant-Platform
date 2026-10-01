import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class LayoutService {
  private _collapsed   = signal(false);
  private _mobileOpen  = signal(false);

  readonly collapsed   = this._collapsed.asReadonly();
  readonly mobileOpen  = this._mobileOpen.asReadonly();

  toggleSidebar(): void {
    if (window.innerWidth < 992) {
      this._mobileOpen.update(v => !v);
    } else {
      this._collapsed.update(v => !v);
    }
  }

  closeMobileSidebar(): void {
    this._mobileOpen.set(false);
  }
}
