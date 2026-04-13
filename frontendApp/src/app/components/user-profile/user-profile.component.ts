import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ModalController, ToastController, AlertController, LoadingController } from '@ionic/angular';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/auth.models';

@Component({
    selector: 'app-user-profile',
    templateUrl: './user-profile.component.html',
    styleUrls: ['./user-profile.component.scss'],
    standalone: false
})
export class UserProfileComponent implements OnInit {
  user: User | null = null;
  showChangePassword = false;
  changePasswordForm!: FormGroup;
  credentialForm!: FormGroup;
  editCredentialForm!: FormGroup;
  loading = false;

  // Admin user management
  showUserManagement = false;
  allUsers: User[] = [];
  loadingUsers = false;
  selectedUser: User | null = null;

  // Credentials management
  showCredentials = false;
  editingCredential: string | null = null;

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private modalController: ModalController,
    private toastController: ToastController,
    private alertController: AlertController,
    private loadingController: LoadingController,
    private router: Router
  ) {}

  ngOnInit() {
    // Get current user
    this.authService.currentUser$.subscribe(user => {
      this.user = user;
    });

    // Initialize change password form
    this.changePasswordForm = this.formBuilder.group({
      currentPassword: ['', [Validators.required]],
      newPassword: ['', [
        Validators.required,
        Validators.minLength(8)
      ]],
      confirmPassword: ['', [Validators.required]]
    });

    // Initialize credential form
    this.credentialForm = this.formBuilder.group({
      credentialKey: ['', [Validators.required]],
      credentialValue: ['', [Validators.required]]
    });

    // Initialize edit credential form
    this.editCredentialForm = this.formBuilder.group({
      credentialValueEdit: ['', [Validators.required]]
    });
  }

  /**
   * Close the modal
   */
  dismiss() {
    this.modalController.dismiss();
  }

  /**
   * Toggle change password section
   */
  toggleChangePassword() {
    this.showChangePassword = !this.showChangePassword;
    if (!this.showChangePassword) {
      this.changePasswordForm.reset();
    }
  }

  /**
   * Handle change password form submission
   */
  async onChangePassword() {
    if (this.changePasswordForm.invalid) {
      this.markFormGroupTouched(this.changePasswordForm);
      return;
    }

    const { currentPassword, newPassword, confirmPassword } = this.changePasswordForm.value;

    if (newPassword !== confirmPassword) {
      const toast = await this.toastController.create({
        message: 'New passwords do not match',
        duration: 3000,
        color: 'danger',
        position: 'top'
      });
      await toast.present();
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Changing password...',
    });
    await loading.present();

    this.loading = true;

    this.authService.changePassword(currentPassword, newPassword).subscribe({
      next: async (response) => {
        await loading.dismiss();
        this.loading = false;
        this.showChangePassword = false;
        this.changePasswordForm.reset();

        const toast = await this.toastController.create({
          message: 'Password changed successfully',
          duration: 3000,
          color: 'success',
          position: 'top'
        });
        await toast.present();
      },
      error: async (error) => {
        await loading.dismiss();
        this.loading = false;

        const toast = await this.toastController.create({
          message: error.message || 'Failed to change password',
          duration: 3000,
          color: 'danger',
          position: 'top'
        });
        await toast.present();
      }
    });
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
            this.modalController.dismiss();
          }
        }
      ]
    });

    await alert.present();
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
      this.modalController.dismiss();
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

  /**
   * Mark all form fields as touched to show validation errors
   */
  private markFormGroupTouched(formGroup: FormGroup) {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();
    });
  }

  /**
   * Get formatted date
   */
  getFormattedDate(dateString: string | null): string {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Check if current user is admin
   */
  isAdmin(): boolean {
    return this.user?.role === 'admin';
  }

  // ==================== CREDENTIALS MANAGEMENT ====================

  /**
   * Toggle credentials section
   */
  toggleCredentials() {
    this.showCredentials = !this.showCredentials;
    if (!this.showCredentials) {
      this.resetCredentialForm();
    }
  }

  /**
   * Get user credentials as key-value pairs
   */
  getCredentials(): Array<{key: string, value: string}> {
    if (!this.user?.config?.credentials) return [];
    return Object.entries(this.user.config.credentials).map(([key, value]) => ({key, value}));
  }

  /**
   * Track function for credentials ngFor to prevent unnecessary re-renders
   */
  trackByCredentialKey(index: number, credential: {key: string, value: string}): string {
    return credential.key;
  }

  /**
   * Add new credential
   */
  async addCredential() {
    if (this.credentialForm.invalid) {
      this.markFormGroupTouched(this.credentialForm);
      return;
    }

    const { credentialKey, credentialValue } = this.credentialForm.value;

    if (!this.user?.config) {
      await this.showToast('User config not available', 'danger');
      return;
    }

    // Check if key already exists
    if (this.user.config.credentials && this.user.config.credentials[credentialKey]) {
      await this.showToast('Credential key already exists', 'warning');
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Adding credential...',
    });
    await loading.present();

    try {
      // Initialize credentials if not exists
      if (!this.user.config.credentials) {
        this.user.config.credentials = {};
      }

      // Add new credential
      this.user.config.credentials[credentialKey] = credentialValue;

      // Update user via API
      this.authService.updateUser(this.user.id, { config: this.user.config }).subscribe({
        next: async (updatedUser) => {
          await loading.dismiss();
          // Update local user data
          this.user = updatedUser;
          this.credentialForm.reset();
          await this.showToast('Credential added successfully', 'success');
        },
        error: async (error) => {
          await loading.dismiss();
          // Revert local change
          if (this.user?.config?.credentials) {
            delete this.user.config.credentials[credentialKey];
          }
          await this.showToast('Failed to add credential: ' + error.message, 'danger');
        }
      });
    } catch (error) {
      await loading.dismiss();
      await this.showToast('Failed to add credential', 'danger');
    }
  }

  /**
   * Start editing a credential
   */
  startEditCredential(key: string) {
    this.editingCredential = key;
    const currentValue = this.user?.config?.credentials?.[key] || '';
    this.editCredentialForm.reset();
    this.editCredentialForm.get('credentialValueEdit')?.setValue(currentValue);
  }

  /**
   * Cancel editing credential
   */
  cancelEditCredential() {
    this.editingCredential = null;
    this.editCredentialForm.reset();
  }

  /**
   * Save edited credential
   */
  async saveEditedCredential() {
    if (this.editCredentialForm.invalid) {
      this.markFormGroupTouched(this.editCredentialForm);
      return;
    }

    if (!this.editingCredential) {
      await this.showToast('No credential selected for editing', 'warning');
      return;
    }

    if (!this.user?.config?.credentials) {
      await this.showToast('User config not available', 'danger');
      return;
    }

    const { credentialValueEdit } = this.editCredentialForm.value;
    const loading = await this.loadingController.create({
      message: 'Updating credential...',
    });
    await loading.present();

    const oldValue = this.user.config.credentials[this.editingCredential];

    try {
      // Update credential value
      this.user.config.credentials[this.editingCredential] = credentialValueEdit;

      // Update user via API
      this.authService.updateUser(this.user.id, { config: this.user.config }).subscribe({
        next: async (updatedUser) => {
          await loading.dismiss();
          // Update local user data
          this.user = updatedUser;
          this.cancelEditCredential();
          await this.showToast('Credential updated successfully', 'success');
        },
        error: async (error) => {
          await loading.dismiss();
          // Revert local change
          if (this.user?.config?.credentials) {
            this.user.config.credentials[this.editingCredential!] = oldValue;
          }
          this.cancelEditCredential();
          await this.showToast('Failed to update credential: ' + error.message, 'danger');
        }
      });
    } catch (error) {
      await loading.dismiss();
      this.cancelEditCredential();
      await this.showToast('Failed to update credential', 'danger');
    }
  }

  /**
   * Delete credential
   */
  async deleteCredential(key: string) {
    const alert = await this.alertController.create({
      header: 'Delete Credential',
      message: `Are you sure you want to delete the credential "${key}"?`,
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Delete',
          role: 'destructive',
          handler: async () => {
            if (!this.user?.config?.credentials) {
              await this.showToast('User config not available', 'danger');
              return;
            }

            const loading = await this.loadingController.create({
              message: 'Deleting credential...',
            });
            await loading.present();

            const oldValue = this.user.config.credentials[key];

            try {
              // Remove credential
              delete this.user.config.credentials[key];

              // Update user via API
              this.authService.updateUser(this.user.id, { config: this.user.config }).subscribe({
                next: async (updatedUser) => {
                  await loading.dismiss();
                  // Update local user data
                  this.user = updatedUser;
                  await this.showToast('Credential deleted successfully', 'success');
                },
                error: async (error) => {
                  await loading.dismiss();
                  // Revert local change
                  if (this.user?.config?.credentials) {
                    this.user.config.credentials[key] = oldValue;
                  }
                  await this.showToast('Failed to delete credential: ' + error.message, 'danger');
                }
              });
            } catch (error) {
              await loading.dismiss();
              await this.showToast('Failed to delete credential', 'danger');
            }
          }
        }
      ]
    });

    await alert.present();
  }

    /**
   * Reset credential editing state
   */
  private resetCredentialForm() {
    this.editingCredential = null;
    this.editCredentialForm.reset();
  }

  // ==================== ADMIN USER MANAGEMENT ====================

  /**
   * Toggle user management section
   */
  async toggleUserManagement() {
    this.showUserManagement = !this.showUserManagement;

    if (this.showUserManagement && this.allUsers.length === 0) {
      await this.loadAllUsers();
    }
  }

  /**
   * Load all users
   */
  async loadAllUsers() {
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
                await this.loadAllUsers();
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
                await this.loadAllUsers();
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
                await this.loadAllUsers();
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
  async createNewUser() {
    await this.modalController.dismiss();
    this.router.navigate(['/register']);
  }
}
