import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ToastController, LoadingController, IonBackButton, IonButton, IonButtons, IonContent, IonHeader, IonIcon, IonInput, IonInputPasswordToggle, IonItem, IonSpinner, IonTitle, IonToolbar } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { alertCircleOutline, atOutline, checkmarkCircle, closeCircle, lockClosedOutline, mailOutline, personAdd, personOutline } from 'ionicons/icons';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../services/auth.service';

/**
 * Message of each field error, checked in this order: the first error found is displayed
 */
const FIELD_ERROR_MESSAGES: ReadonlyArray<[string, (label: string, error: any) => string]> = [
  ['required', (label) => `${label} is required`],
  ['minlength', (label, error) => `${label} must be at least ${error.requiredLength} characters`],
  ['maxlength', (label, error) => `${label} must not exceed ${error.requiredLength} characters`],
  ['email', () => 'Please enter a valid email address'],
  ['pattern', () => 'Username can only contain letters, numbers, hyphens, and underscores'],
  ['passwordStrength', () => 'Password must meet strength requirements'],
];

@Component({
    selector: 'app-register',
    templateUrl: './register.page.html',
    styleUrls: ['./register.page.scss'],
    imports: [IonBackButton, IonButton, IonButtons, IonContent, IonHeader, IonIcon, IonInput, IonInputPasswordToggle, IonItem, IonSpinner, IonTitle, IonToolbar, FormsModule, ReactiveFormsModule]
})
export class RegisterPage implements OnInit {
  private readonly formBuilder = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly toastController = inject(ToastController);
  private readonly loadingController = inject(LoadingController);

  registerForm!: FormGroup;
  loading = false;

  constructor() {
    addIcons({ alertCircleOutline, atOutline, checkmarkCircle, closeCircle, lockClosedOutline, mailOutline, personAdd, personOutline });
    // Initialize form synchronously to avoid template errors
    this.registerForm = this.formBuilder.group({
      username: ['', [
        Validators.required,
        Validators.minLength(3),
        Validators.maxLength(50),
        Validators.pattern(/^[a-zA-Z0-9_-]+$/)
      ]],
      email: ['', [
        Validators.required,
        Validators.email
      ]],
      firstName: ['', [
        Validators.required,
        Validators.minLength(2)
      ]],
      lastName: ['', [
        Validators.required,
        Validators.minLength(2)
      ]],
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

  ngOnInit() {
    this.restoreSession().catch(error => console.error('Failed to restore the session:', error));
  }

  /**
   * Try to restore the session: this page is not protected by a guard and does not load the user automatically,
   * but some restrictions (e.g. .env config) can require an admin user to create an account.
   */
  private async restoreSession(): Promise<void> {
    const hasTokens = await this.authService.isAuthenticated();
    if (hasTokens && !this.authService.currentUserValue) {
      await this.authService.loadCurrentUser();
    }
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
    const hasNumber = /[0-9]/.test(value);
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
    if (this.registerForm.invalid) {
      this.markFormGroupTouched(this.registerForm);
      return;
    }

    const { username, email, firstName, lastName, password } = this.registerForm.value;

    const loading = await this.loadingController.create({
      message: 'Creating account...',
    });
    await loading.present();

    this.loading = true;

    const failure = await firstValueFrom(this.authService.register({
      username,
      email,
      full_name: `${firstName} ${lastName}`,
      password
    })).then(() => null, (error: Error) => error);

    await loading.dismiss();
    this.loading = false;

    if (failure) {
      const toast = await this.toastController.create({
        message: failure.message || 'Registration failed. Please try again.',
        duration: 3000,
        color: 'danger',
        position: 'top'
      });
      await toast.present();
      return;
    }

    const toast = await this.toastController.create({
      message: 'Account created successfully! Please check your email to activate your account.',
      duration: 5000,
      color: 'success',
      position: 'top'
    });
    await toast.present();

    // Redirect to login page
    await this.router.navigate(['/login']);
  }

  /**
   * Navigate to login page
   */
  goToLogin() {
    this.router.navigate(['/login']);
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
    const field = this.registerForm.get(fieldName);

    if (field?.touched && field?.errors) {
      const message = this.getControlErrorMessage(fieldName, field.errors);
      if (message) {
        return message;
      }
    }

    // Check form-level errors
    if (fieldName === 'confirmPassword' && this.registerForm.errors?.['passwordMismatch'] && field?.touched) {
      return 'Passwords do not match';
    }

    return null;
  }

  /**
   * Message of the first error of a field, in the order of FIELD_ERROR_MESSAGES
   */
  private getControlErrorMessage(fieldName: string, errors: ValidationErrors): string | null {
    const entry = FIELD_ERROR_MESSAGES.find(([errorKey]) => errors[errorKey]);
    return entry ? entry[1](this.getFieldLabel(fieldName), errors[entry[0]]) : null;
  }

  /**
   * Get password strength requirements that are not met
   */
  getPasswordStrengthErrors(): string[] {
    const passwordControl = this.registerForm.get('password');
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
      username: 'Username',
      email: 'Email',
      firstName: 'First Name',
      lastName: 'Last Name',
      password: 'Password',
      confirmPassword: 'Confirm Password'
    };
    return labels[fieldName] || fieldName;
  }
}
