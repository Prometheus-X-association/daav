import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, ToastController, IonBadge, IonButton, IonIcon, IonNote, IonSpinner } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { eyeOffOutline, eyeOutline, keyOutline, peopleOutline, personAddOutline, refreshOutline, trashOutline } from 'ionicons/icons';
import { AuthService } from '../../../services/auth.service';
import { User } from '../../../models/auth.models';
import { formatAccountDate } from '../account-utils';
import { UpperCasePipe } from '@angular/common';

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
      error: async (error) => {
        this.loadingUsers = false;
        await this.showToast('Failed to load users: ' + error.message, 'danger');
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
            this.authService.deactivateUser(user.id, data.reason).subscribe({
              next: async () => {
                await this.showToast(`User ${user.username} deactivated successfully`, 'success');
                this.loadAllUsers();
              },
              error: async (error) => {
                await this.showToast('Failed to deactivate user: ' + error.message, 'danger');
              }
            });
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
            this.authService.activateUser(user.id).subscribe({
              next: async () => {
                await this.showToast(`User ${user.username} activated successfully`, 'success');
                this.loadAllUsers();
              },
              error: async (error) => {
                await this.showToast('Failed to activate user: ' + error.message, 'danger');
              }
            });
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
            this.authService.deleteUser(user.id).subscribe({
              next: async () => {
                await this.showToast(`User ${user.username} deleted successfully`, 'success');
                this.loadAllUsers();
              },
              error: async (error) => {
                await this.showToast('Failed to delete user: ' + error.message, 'danger');
              }
            });
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
              this.showToast('Password must be at least 8 characters', 'warning');
              return false;
            }
            if (data.newPassword !== data.confirmPassword) {
              this.showToast('Passwords do not match', 'warning');
              return false;
            }

            // Use updateUser to change password via PUT /auth/users/{id}
            this.authService.updateUser(user.id, { password: data.newPassword }).subscribe({
              next: async () => {
                await this.showToast(`Password changed successfully for ${user.username}`, 'success');
              },
              error: async (error) => {
                await this.showToast('Failed to change password: ' + error.message, 'danger');
              }
            });
            return true;
          }
        }
      ]
    });

    await alert.present();
  }

  /**
   * Navigate to create user (register page)
   */
  createNewUser() {
    this.router.navigate(['/register']);
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
