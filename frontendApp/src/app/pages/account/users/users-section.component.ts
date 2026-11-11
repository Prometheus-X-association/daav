import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, ToastController, IonBadge, IonButton, IonIcon, IonNote, IonSpinner } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { eyeOffOutline, eyeOutline, keyOutline, peopleOutline, personAddOutline, refreshOutline, trashOutline } from 'ionicons/icons';
import { AuthService } from '../../../services/auth.service';
import { User } from '../../../models/auth.models';
import { formatAccountDate } from '../account-utils';
import { UpperCasePipe } from '@angular/common';
import { Observable } from 'rxjs';

/**
 * Account page section: user management (Admin only)
 */
@Component({
    selector: 'app-users-section',
    templateUrl: './users-section.component.html',
    styleUrls: ['./users-section.component.scss'],
    imports: [IonBadge, IonButton, IonIcon, IonNote, IonSpinner, UpperCasePipe]
})
export class UsersSectionComponent implements OnInit {
  private readonly authService = inject(AuthService);
  private readonly toastController = inject(ToastController);
  private readonly alertController = inject(AlertController);
  private readonly router = inject(Router);

  allUsers: User[] = [];
  loadingUsers = false;

  constructor() {
    addIcons({ eyeOffOutline, eyeOutline, keyOutline, peopleOutline, personAddOutline, refreshOutline, trashOutline });
  }

  ngOnInit() {
    this.loadAllUsers();
  }

  get currentUserId(): string | undefined {
    return this.authService.currentUserValue?.id;
  }

  getFormattedDate(dateString: string | null): string {
    return formatAccountDate(dateString, true);
  }

  getFullDate(dateString: string | null): string {
    return formatAccountDate(dateString);
  }

  /**
   * Load all users
   */
  loadAllUsers() {
    this.loadingUsers = true;

    this.authService.getAllUsers().subscribe({
      next: (users) => {
        this.allUsers = users;
        this.loadingUsers = false;
      },
      error: (error) => {
        this.loadingUsers = false;
        void this.showToast('Failed to load users: ' + error.message, 'danger');
      }
    });
  }

  /**
   * Deactivate user
   */
  async deactivateUser(user: User) {
    const alert = await this.alertController.create({
      header: 'Deactivate User',
      message: `Are you sure you want to deactivate ${user.username}?`,
      inputs: [
        {
          name: 'reason',
          type: 'textarea',
          placeholder: 'Reason for deactivation (optional)'
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
            this.runUserAction(
              this.authService.deactivateUser(user.id, data.reason),
              `User ${user.username} deactivated successfully`,
              'Failed to deactivate user: '
            );
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Activate user
   */
  async activateUser(user: User) {
    const alert = await this.alertController.create({
      header: 'Activate User',
      message: `Are you sure you want to activate ${user.username}?`,
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Activate',
          handler: () => {
            this.runUserAction(
              this.authService.activateUser(user.id),
              `User ${user.username} activated successfully`,
              'Failed to activate user: '
            );
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Delete user
   */
  async deleteUser(user: User) {
    const alert = await this.alertController.create({
      header: 'Delete User',
      message: `Are you sure you want to permanently delete ${user.username}? This action cannot be undone.`,
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Delete',
          role: 'destructive',
          handler: () => {
            this.runUserAction(
              this.authService.deleteUser(user.id),
              `User ${user.username} deleted successfully`,
              'Failed to delete user: '
            );
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Change user password (Admin)
   */
  async changeUserPassword(user: User) {
    const alert = await this.alertController.create({
      header: 'Change Password',
      message: `Change password for ${user.username}`,
      inputs: [
        {
          name: 'newPassword',
          type: 'password',
          placeholder: 'New password (min 8 characters)',
          attributes: {
            minlength: 8
          }
        },
        {
          name: 'confirmPassword',
          type: 'password',
          placeholder: 'Confirm new password'
        }
      ],
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Change',
          handler: (data) => {
            if (!data.newPassword || data.newPassword.length < 8) {
              void this.showToast('Password must be at least 8 characters', 'warning');
              return false;
            }
            if (data.newPassword !== data.confirmPassword) {
              void this.showToast('Passwords do not match', 'warning');
              return false;
            }

            // Use updateUser to change password via PUT /auth/users/{id}
            this.runUserAction(
              this.authService.updateUser(user.id, { password: data.newPassword }),
              `Password changed successfully for ${user.username}`,
              'Failed to change password: ',
              false
            );
            return true;
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Run an action on a user and report its result, then reload the users if requested
   */
  private runUserAction(action: Observable<unknown>, successMessage: string, errorPrefix: string, reloadUsers = true) {
    action.subscribe({
      next: () => {
        void this.showToast(successMessage, 'success');
        if (reloadUsers) {
          this.loadAllUsers();
        }
      },
      error: (error) => {
        void this.showToast(errorPrefix + error.message, 'danger');
      }
    });
  }

  /**
   * Navigate to create user (register page)
   */
  createNewUser() {
    this.router.navigate(['/register']);
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
