import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { filter } from 'rxjs';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/auth.models';

export interface AccountSection {
  path: string;
  label: string;
  icon: string;
  description: string;
  adminOnly?: boolean;
}

/**
 * Account administration page
 * Side menu listing the sections, the selected section is displayed in the central panel
 */
@Component({
    selector: 'app-account',
    templateUrl: './account.page.html',
    styleUrls: ['./account.page.scss'],
    standalone: false
})
export class AccountPage implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  user: User | null = null;
  currentSection: AccountSection | undefined;

  readonly sections: AccountSection[] = [
    {
      path: 'profile',
      label: 'Profile',
      icon: 'person-outline',
      description: 'Your account information.'
    },
    {
      path: 'security',
      label: 'Security',
      icon: 'lock-closed-outline',
      description: 'Change the password of your account.'
    },
    {
      path: 'credentials',
      label: 'Credentials',
      icon: 'key-outline',
      description: 'HTTP headers authenticating machine-to-machine calls to your API outputs.'
    },
    {
      path: 'users',
      label: 'Users',
      icon: 'people-outline',
      description: 'Manage the user accounts of the platform.',
      adminOnly: true
    }
  ];

  constructor(
    private authService: AuthService,
    private alertController: AlertController,
    private router: Router
  ) {}

  ngOnInit() {
    this.authService.currentUser$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(user => {
        this.user = user;
      });

    this.updateCurrentSection();
    this.router.events
      .pipe(
        filter(event => event instanceof NavigationEnd),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe(() => this.updateCurrentSection());
  }

  /**
   * Sections the current user can access
   */
  get visibleSections(): AccountSection[] {
    return this.sections.filter(section => !section.adminOnly || this.user?.role === 'admin');
  }

  private updateCurrentSection() {
    const path = this.router.url.split(/[?#]/)[0].split('/').pop();
    this.currentSection = this.sections.find(section => section.path === path);
  }

  /**
   * Handle logout
   */
  async onLogout() {
    const alert = await this.alertController.create({
      header: 'Logout',
      message: 'Are you sure you want to logout?',
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Logout',
          role: 'destructive',
          handler: () => {
            this.authService.logout();
          }
        }
      ]
    });

    await alert.present();
  }
}
