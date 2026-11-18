import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ToastController, LoadingController, IonBackButton, IonButton, IonButtons, IonContent, IonHeader, IonIcon, IonInput, IonItem, IonSpinner, IonTitle, IonToolbar } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { alertCircleOutline, arrowBackOutline, checkmarkCircle, informationCircleOutline, mailOutline, mailUnread, refreshOutline } from 'ionicons/icons';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-forgot-password',
    templateUrl: './forgot-password.page.html',
    styleUrls: ['./forgot-password.page.scss'],
    imports: [IonBackButton, IonButton, IonButtons, IonContent, IonHeader, IonIcon, IonInput, IonItem, IonSpinner, IonTitle, IonToolbar, FormsModule, ReactiveFormsModule]
})
export class ForgotPasswordPage implements OnInit {
  private readonly formBuilder = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly toastController = inject(ToastController);
  private readonly loadingController = inject(LoadingController);

  forgotPasswordForm!: FormGroup;
  loading = false;
  emailSent = false;

  constructor() {
    addIcons({ alertCircleOutline, arrowBackOutline, checkmarkCircle, informationCircleOutline, mailOutline, mailUnread, refreshOutline });
  }

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

    const failure = await firstValueFrom(this.authService.forgotPassword(email))
      .then(() => null, (error: Error) => error);

    await loading.dismiss();
    this.loading = false;

    if (failure) {
      const toast = await this.toastController.create({
        message: failure.message || 'Failed to send reset email. Please try again.',
        duration: 3000,
        color: 'danger',
        position: 'top'
      });
      await toast.present();
      return;
    }

    this.emailSent = true;

    const toast = await this.toastController.create({
      message: 'Password reset instructions have been sent to your email.',
      duration: 5000,
      color: 'success',
      position: 'top'
    });
    await toast.present();
  }

  /**
   * Navigate back to login page
   */
  goToLogin() {
    void this.router.navigate(['/login']);
  }

  /**
   * Resend email
   */
  async resendEmail() {
    this.emailSent = false;
    await this.onSubmit();
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
