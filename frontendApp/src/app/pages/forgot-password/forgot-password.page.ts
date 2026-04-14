import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { ToastController, LoadingController } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-forgot-password',
    templateUrl: './forgot-password.page.html',
    styleUrls: ['./forgot-password.page.scss'],
    standalone: false
})
export class ForgotPasswordPage implements OnInit {
  forgotPasswordForm!: FormGroup;
  loading = false;
  emailSent = false;

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private toastController: ToastController,
    private loadingController: LoadingController
  ) {}

  ngOnInit() {
    this.forgotPasswordForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  /**
   * Handle form submission
   */
  async onSubmit() {
    if (this.forgotPasswordForm.invalid) {
      this.markFormGroupTouched(this.forgotPasswordForm);
      return;
    }

    const { email } = this.forgotPasswordForm.value;

    const loading = await this.loadingController.create({
      message: 'Sending reset email...',
    });
    await loading.present();

    this.loading = true;

    this.authService.forgotPassword(email).subscribe({
      next: async (response) => {
        await loading.dismiss();
        this.loading = false;
        this.emailSent = true;

        const toast = await this.toastController.create({
          message: 'Password reset instructions have been sent to your email.',
          duration: 5000,
          color: 'success',
          position: 'top'
        });
        await toast.present();
      },
      error: async (error) => {
        await loading.dismiss();
        this.loading = false;

        const toast = await this.toastController.create({
          message: error.message || 'Failed to send reset email. Please try again.',
          duration: 3000,
          color: 'danger',
          position: 'top'
        });
        await toast.present();
      }
    });
  }

  /**
   * Navigate back to login page
   */
  goToLogin() {
    this.router.navigate(['/login']);
  }

  /**
   * Resend email
   */
  resendEmail() {
    this.emailSent = false;
    this.onSubmit();
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
   * Get form field errors for display
   */
  getFieldError(fieldName: string): string | null {
    const field = this.forgotPasswordForm.get(fieldName);

    if (field?.touched && field?.errors) {
      if (field.errors['required']) {
        return 'Email is required';
      }
      if (field.errors['email']) {
        return 'Please enter a valid email address';
      }
    }

    return null;
  }
}
