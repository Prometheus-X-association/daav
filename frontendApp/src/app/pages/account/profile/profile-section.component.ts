import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AlertController, LoadingController, ToastController } from '@ionic/angular';
import { AuthService } from '../../../services/auth.service';
import { User } from '../../../models/auth.models';
import { formatAccountDate } from '../account-utils';

/**
 * Account page section: information of the current user
 */
@Component({
    selector: 'app-profile-section',
    templateUrl: './profile-section.component.html',
    styleUrls: ['./profile-section.component.scss'],
    standalone: false
})
export class ProfileSectionComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  user: User | null = null;

  constructor(
    private authService: AuthService,
    private toastController: ToastController,
    private alertController: AlertController,
    private loadingController: LoadingController
  ) {}

  ngOnInit() {
    this.authService.currentUser$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(user => {
        this.user = user;
      });
  }

  getFormattedDate(dateString: string | null): string {
    return formatAccountDate(dateString);
  }

  /**
   * Handle account deactivation
   */
  async onDeactivateAccount() {
    const alert = await this.alertController.create({
      header: 'Deactivate Account',
      message: 'Are you sure you want to deactivate your account? This action cannot be undone.',
      inputs: [
        {
          name: 'confirmation',
          type: 'text',
          placeholder: 'Type "DEACTIVATE" to confirm'
        }
      ],
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Deactivate',
          role: 'destructive',
          handler: (data) => {
            if (data.confirmation === 'DEACTIVATE') {
              this.deactivateAccount();
              return true;
            } else {
              this.showToast('Please type "DEACTIVATE" to confirm', 'warning');
              return false;
            }
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Deactivate account
   */
  private async deactivateAccount() {
    const loading = await this.loadingController.create({
      message: 'Deactivating account...',
    });
    await loading.present();

    // TODO: Implement deactivation API call
    setTimeout(async () => {
      await loading.dismiss();
      this.showToast('Account deactivated successfully', 'success');
      this.authService.logout();
    }, 1000);
  }

  /**
   * Show toast message
   */
  private async showToast(message: string, color: string = 'primary') {
    const toast = await this.toastController.create({
      message,
      duration: 3000,
      color,
      position: 'top'
    });
    await toast.present();
  }
}
