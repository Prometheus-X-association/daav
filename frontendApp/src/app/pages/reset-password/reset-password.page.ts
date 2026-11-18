import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { ToastController, LoadingController, AlertController, IonButton, IonContent, IonHeader, IonIcon, IonInput, IonInputPasswordToggle, IonItem, IonSpinner, IonTitle, IonToolbar } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { alertCircle, alertCircleOutline, arrowBackOutline, checkmarkCircle, closeCircle, key, lockClosedOutline, mailOutline } from 'ionicons/icons';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-reset-password',
    templateUrl: './reset-password.page.html',
    styleUrls: ['./reset-password.page.scss'],
    imports: [IonButton, IonContent, IonHeader, IonIcon, IonInput, IonInputPasswordToggle, IonItem, IonSpinner, IonTitle, IonToolbar, FormsModule, ReactiveFormsModule]
})
export class ResetPasswordPage implements OnInit {
  private readonly formBuilder = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly toastController = inject(ToastController);
  private readonly loadingController = inject(LoadingController);
  private readonly alertController = inject(AlertController);

  resetPasswordForm!: FormGroup;
  loading = false;
  token: string = '';
  tokenValid = true;

  constructor() {
    addIcons({ alertCircle, alertCircleOutline, arrowBackOutline, checkmarkCircle, closeCircle, key, lockClosedOutline, mailOutline });
  }

  ngOnInit() {
    // Get token from query parameters
    this.token = this.route.snapshot.queryParams['token'] || '';

    if (!this.token) {
      this.tokenValid = false;
      this.showInvalidTokenAlert().catch(error => console.error('Failed to show the invalid link alert:', error));
      return;
    }

    // Initialize form
    this.resetPasswordForm = this.formBuilder.group({
      password: ['', [
        Validators.required,
        Validators.minLength(8),
        this.passwordStrengthValidator
      ]],
      confirmPassword: ['', [
        Validators.required
      ]]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  /**
   * Custom validator for password strength
   */
  private passwordStrengthValidator(control: AbstractControl): ValidationErrors | null {
    const value = control.value;

    if (!value) {
      return null;
    }

    const hasUpperCase = /[A-Z]/.test(value);
    const hasLowerCase = /[a-z]/.test(value);
    const hasNumber = /\d/.test(value);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(value);

    const passwordValid = hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;

    return !passwordValid ? {
      passwordStrength: {
        hasUpperCase,
        hasLowerCase,
        hasNumber,
        hasSpecialChar
      }
    } : null;
  }

  /**
   * Custom validator to check if passwords match
   */
  private passwordMatchValidator(group: AbstractControl): ValidationErrors | null {
    const password = group.get('password')?.value;
    const confirmPassword = group.get('confirmPassword')?.value;

    return password === confirmPassword ? null : { passwordMismatch: true };
  }

  /**
   * Handle form submission
   */
  async onSubmit() {
    if (this.resetPasswordForm.invalid) {
      this.markFormGroupTouched(this.resetPasswordForm);
      return;
    }

    const { password } = this.resetPasswordForm.value;

    const loading = await this.loadingController.create({
      message: 'Resetting password...',
    });
    await loading.present();

    this.loading = true;

    const failure = await firstValueFrom(this.authService.resetPassword(this.token, password))
      .then(() => null, (error: Error) => error);

    await loading.dismiss();
    this.loading = false;

    if (failure) {
      let message = 'Failed to reset password. Please try again.';

      if (failure.message) {
        message = failure.message;
      }

      // Check if token is expired or invalid
      if (failure.message?.toLowerCase().includes('expired') ||
          failure.message?.toLowerCase().includes('invalid')) {
        this.tokenValid = false;
        message += ' Please request a new password reset link.';
      }

      const toast = await this.toastController.create({
        message,
        duration: 5000,
        color: 'danger',
        position: 'top'
      });
      await toast.present();
      return;
    }

    const alert = await this.alertController.create({
      header: 'Success!',
      message: 'Your password has been reset successfully. You can now log in with your new password.',
      buttons: [
        {
          text: 'Go to Login',
          handler: () => {
            this.router.navigate(['/login'])
              .catch(error => console.error('Failed to navigate to the login page:', error));
          }
        }
      ]
    });
    await alert.present();
  }

  /**
   * Show alert for invalid token
   */
  async showInvalidTokenAlert() {
    const alert = await this.alertController.create({
      header: 'Invalid Link',
      message: 'This password reset link is invalid or has expired. Please request a new one.',
      buttons: [
        {
          text: 'Go to Forgot Password',
          handler: () => {
            this.router.navigate(['/forgot-password'])
              .catch(error => console.error('Failed to navigate to the forgot password page:', error));
          }
        }
      ]
    });
    await alert.present();
  }

  /**
   * Navigate to forgot password page
   */
  goToForgotPassword() {
    void this.router.navigate(['/forgot-password']);
  }

  /**
   * Navigate to login page
   */
  goToLogin() {
    void this.router.navigate(['/login']);
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
    const field = this.resetPasswordForm.get(fieldName);

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
    if (fieldName === 'confirmPassword' && this.resetPasswordForm.errors?.['passwordMismatch'] && field?.touched) {
      return 'Passwords do not match';
    }

    return null;
  }

  /**
   * Get password strength requirements that are not met
   */
  getPasswordStrengthErrors(): string[] {
    const passwordControl = this.resetPasswordForm.get('password');
    const errors: string[] = [];

    if (passwordControl?.errors?.['passwordStrength']) {
      const strength = passwordControl.errors['passwordStrength'];
      if (!strength.hasUpperCase) errors.push('one uppercase letter');
      if (!strength.hasLowerCase) errors.push('one lowercase letter');
      if (!strength.hasNumber) errors.push('one number');
      if (!strength.hasSpecialChar) errors.push('one special character');
    }

    return errors;
  }

  /**
   * Get user-friendly field label
   */
  private getFieldLabel(fieldName: string): string {
    const labels: { [key: string]: string } = {
      password: 'Password',
      confirmPassword: 'Confirm Password'
    };
    return labels[fieldName] || fieldName;
  }
}
