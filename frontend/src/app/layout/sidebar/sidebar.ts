import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { LayoutService } from '../../services/layout.service';
import { AuthService } from '../../services/auth.service';

interface NavItem {
  label: string;
  icon: string;
  route: string;
  badge?: string;
  badgeClass?: string;
  exact?: boolean;
  roles?: string[];   // undefined = all roles
}

interface NavSection {
  label: string;
  items: NavItem[];
  roles?: string[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss'
})
export class Sidebar {
  layout = inject(LayoutService);
  auth   = inject(AuthService);

  readonly appVersion = '15.21.12';

  private readonly allSections: NavSection[] = [
    {
      label: 'MAIN',
      items: [
        { label: 'Dashboard', icon: 'pi-chart-bar', route: '/dashboard', exact: true },
        { label: 'Profile',   icon: 'pi-user-edit', route: '/dashboard/profile' }
      ]
    },
    {
      label: 'HGW ENTRIES',
      roles: ['admin', 'engineer'],
      items: [
        { label: 'My Entries',    icon: 'pi-list',        route: '/dashboard/entries' },
        { label: 'Add Entry',     icon: 'pi-plus-circle', route: '/dashboard/entries/add' }
      ]
    },
    {
      label: 'AI ASSISTANT',
      items: [
        { 
          label: 'AI Chat',
          icon: 'pi-comments',
          route: '/dashboard/chat',
          badge: 'GPT-OSS 120B',
          badgeClass: 'badge-info'
        }
      ]
    },
    {
      label: 'ADMINISTRATION',
      roles: ['admin'],
      items: [
        { label: 'Users',            icon: 'pi-users',       route: '/dashboard/admin/users' },
        { label: 'Account Requests', icon: 'pi-user-plus',   route: '/dashboard/admin/requests' },
        { label: 'Logs',             icon: 'pi-list',        route: '/dashboard/admin/conversations' },
        { label: 'Analytics',        icon: 'pi-chart-line',  route: '/dashboard/admin/analytics' },
        { label: 'Prompts',          icon: 'pi-sliders-h',   route: '/dashboard/admin/prompts' }
      ]
    }
  ];

  get navSections(): NavSection[] {
    const role = this.auth.getRole() ?? 'general';
    return this.allSections.filter(s => !s.roles || s.roles.includes(role));
  }

  get currentUser() {
    return {
      username: this.auth.getUsername(),
      role: this.auth.getRole()
    };
  }

  logout() {
    this.auth.logout();
  }
}