import { Component, DestroyRef, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { AlertController, LoadingController, ToastController, IonBadge, IonButton, IonIcon, IonSpinner } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { atOutline, calendarOutline, informationCircleOutline, mailOutline, personOutline, shieldOutline, timeOutline, trashOutline } from 'ionicons/icons';
import { AuthService } from '../../../services/auth.service';
import { User } from '../../../models/auth.models';
import { formatAccountDate } from '../account-utils';
import { UpperCasePipe } from '@angular/common';

/**
 * Account page section: information of the current user
 */
@Component({
    selector: 'app-profile-section',
    templateUrl: './profile-section.component.html',
    styleUrls: ['./profile-section.component.scss'],
    imports: [IonBadge, IonButton, IonIcon, IonSpinner, UpperCasePipe]
})
export class ProfileSectionComponent implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly toastController = inject(ToastController);
  private readonly alertController = inject(AlertController);
  private readonly loadingController = inject(LoadingController);

  private readonly destroyRef = inject(DestroyRef);
  user: User | null = null;

  constructor() {
    addIcons({ atOutline, calendarOutline, informationCircleOutline, mailOutline, personOutline, shieldOutline, timeOutline, trashOutline });
  }

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
              this.deactivateAccount().catch(error => console.error('Failed to deactivate the account:', error));
              return true;
            } else {
              void this.showToast('Please type "DEACTIVATE" to confirm', 'warning');
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
    await new Promise(resolve => setTimeout(resolve, 1000));

    await loading.dismiss();
    void this.showToast('Account deactivated successfully', 'success');
    await this.authService.logout();
  }

  /**
   * Show toast message, a failure is only logged (the toasts are not awaited)
   */
  private async showToast(message: string, color: string = 'primary') {
    try {
      const toast = await this.toastController.create({
        message,
        duration: 3000,
        color,
        position: 'top'
      });
      await toast.present();
    } catch (error) {
      console.error('Failed to show toast:', error);
    }
  }
}
