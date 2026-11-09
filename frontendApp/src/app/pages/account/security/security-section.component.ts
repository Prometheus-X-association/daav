import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { LoadingController, ToastController } from '@ionic/angular';
import { AuthService } from '../../../services/auth.service';

/**
 * Account page section: password of the current user
 */
@Component({
    selector: 'app-security-section',
    templateUrl: './security-section.component.html',
    styleUrls: ['./security-section.component.scss'],
    standalone: false
})
export class SecuritySectionComponent implements OnInit {
  changePasswordForm!: FormGroup;
  loading = false;

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private toastController: ToastController,
    private loadingController: LoadingController
  ) {}

  ngOnInit() {
    this.changePasswordForm = this.formBuilder.group({
      currentPassword: ['', [Validators.required]],
      newPassword: ['', [
        Validators.required,
        Validators.minLength(8)
      ]],
      confirmPassword: ['', [Validators.required]]
    });
  }

  /**
   * Handle change password form submission
   */
  async onChangePassword() {
    if (this.changePasswordForm.invalid) {
      this.changePasswordForm.markAllAsTouched();
      return;
    }

    const { currentPassword, newPassword, confirmPassword } = this.changePasswordForm.value;

    if (newPassword !== confirmPassword) {
      await this.showToast('New passwords do not match', 'danger');
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Changing password...',
    });
    await loading.present();

    this.loading = true;

    this.authService.changePassword(currentPassword, newPassword).subscribe({
      next: async () => {
        await loading.dismiss();
        this.loading = false;
        this.changePasswordForm.reset();
        await this.showToast('Password changed successfully', 'success');
      },
      error: async (error) => {
        await loading.dismiss();
        this.loading = false;
        await this.showToast(error.message || 'Failed to change password', 'danger');
      }
    });
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
