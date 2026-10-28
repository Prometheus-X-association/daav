import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { ToastController, LoadingController } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';

/**
 * Change Password Page
 * Shown when the user must change their password before accessing the application
 * (e.g. first login with the default admin account)
 */
@Component({
    selector: 'app-change-password',
    templateUrl: './change-password.page.html',
    styleUrls: ['./change-password.page.scss'],
    standalone: false
})
export class ChangePasswordPage implements OnInit {
  changePasswordForm!: FormGroup;
  loading = false;
  returnUrl: string = '/';

  constructor(
    private formBuilder: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private toastController: ToastController,
    private loadingController: LoadingController
  ) {}

  ngOnInit() {
    this.changePasswordForm = this.formBuilder.group({
      currentPassword: ['', [Validators.required]],
      newPassword: ['', [
        Validators.required,
        Validators.minLength(8),
        this.passwordStrengthValidator
      ]],
      confirmPassword: ['', [
        Validators.required
      ]]
    }, {
      validators: [this.passwordMatchValidator, this.passwordDifferentValidator]
    });

    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';
  }

  /**
   * Custom validator for password strength (same rules as the backend)
   */
  private passwordStrengthValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;

    if (!value) {
      return null;
    }

    const hasUpperCase = /[A-Z]/.test(value);
    const hasLowerCase = /[a-z]/.test(value);
    const hasSpecialChar = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?\/]/.test(value);

    const passwordValid = hasUpperCase && hasLowerCase && hasSpecialChar;

    return !passwordValid ? {
      passwordStrength: {
        hasUpperCase,
        hasLowerCase,
        hasSpecialChar
      }
    } : null;
  }

  /**
   * Custom validator to check if passwords match
   */
  private passwordMatchValidator(group: AbstractControl): ValidationErrors | null {
    const newPassword = group.get('newPassword')?.value;
    const confirmPassword = group.get('confirmPassword')?.value;

    return newPassword === confirmPassword ? null : { passwordMismatch: true };
  }

  /**
   * Custom validator to check that the new password differs from the current one
   */
  private passwordDifferentValidator(group: AbstractControl): ValidationErrors | null {
    const currentPassword = group.get('currentPassword')?.value;
    const newPassword = group.get('newPassword')?.value;

    return !newPassword || newPassword !== currentPassword ? null : { samePassword: true };
  }

  /**
   * Handle form submission
   */
  async onSubmit() {
    if (this.changePasswordForm.invalid) {
      this.markFormGroupTouched(this.changePasswordForm);
      return;
    }

    const { currentPassword, newPassword } = this.changePasswordForm.value;

    const loading = await this.loadingController.create({
      message: 'Changing password...',
    });
    await loading.present();

    this.loading = true;

    this.authService.changePassword(currentPassword, newPassword).subscribe({
      next: async () => {
        // Reload user to clear the pending password change and load user data
        await this.authService.loadCurrentUser();

        await loading.dismiss();
        this.loading = false;

        const toast = await this.toastController.create({
          message: 'Password changed successfully',
          duration: 3000,
          color: 'success',
          position: 'top'
        });
        await toast.present();

        this.router.navigateByUrl(this.returnUrl, { replaceUrl: true });
      },
      error: async (error) => {
        await loading.dismiss();
        this.loading = false;

        const toast = await this.toastController.create({
          message: error.message || 'Failed to change password',
          duration: 5000,
          color: 'danger',
          position: 'top'
        });
        await toast.present();
      }
    });
  }

  /**
   * Logout without changing the password
   */
  async logout() {
    await this.authService.logout();
  }

  /**
   * Mark all form fields as touched to show validation errors
   */
  private markFormGroupTouched(formGroup: FormGroup) {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      control?.markAsTouched();

      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  /**
   * Get form field errors for display
   */
  getFieldError(fieldName: string): string | null {
    const field = this.changePasswordForm.get(fieldName);

    if (field?.touched && field?.errors) {
      if (field.errors['required']) {
        return `${this.getFieldLabel(fieldName)} is required`;
      }
      if (field.errors['minlength']) {
        const minLength = field.errors['minlength'].requiredLength;
        return `${this.getFieldLabel(fieldName)} must be at least ${minLength} characters`;
      }
      if (field.errors['passwordStrength']) {
        return 'Password must meet strength requirements';
      }
    }

    // Check form-level errors
    if (fieldName === 'newPassword' && this.changePasswordForm.errors?.['samePassword'] && field?.touched) {
      return 'New password must be different from the current password';
    }
    if (fieldName === 'confirmPassword' && this.changePasswordForm.errors?.['passwordMismatch'] && field?.touched) {
      return 'Passwords do not match';
    }

    return null;
  }

  /**
   * Get password strength requirements that are not met
   */
  getPasswordStrengthErrors(): string[] {
    const passwordControl = this.changePasswordForm.get('newPassword');
    const errors: string[] = [];

    if (passwordControl?.errors?.['passwordStrength']) {
      const strength = passwordControl.errors['passwordStrength'];
      if (!strength.hasUpperCase) errors.push('one uppercase letter');
      if (!strength.hasLowerCase) errors.push('one lowercase letter');
      if (!strength.hasSpecialChar) errors.push('one special character');
    }

    return errors;
  }

  /**
   * Get user-friendly field label
   */
  private getFieldLabel(fieldName: string): string {
    const labels: { [key: string]: string } = {
      currentPassword: 'Current Password',
      newPassword: 'New Password',
      confirmPassword: 'Confirm Password'
    };
    return labels[fieldName] || fieldName;
  }
}
