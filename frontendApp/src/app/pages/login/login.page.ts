import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { ToastController, LoadingController, IonButton, IonCheckbox, IonContent, IonHeader, IonIcon, IonInput, IonInputPasswordToggle, IonItem, IonSpinner, IonTitle, IonToolbar } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { alertCircleOutline, lockClosed, lockClosedOutline, personOutline } from 'ionicons/icons';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-login',
    templateUrl: './login.page.html',
    styleUrls: ['./login.page.scss'],
    imports: [IonButton, IonCheckbox, IonContent, IonHeader, IonIcon, IonInput, IonInputPasswordToggle, IonItem, IonSpinner, IonTitle, IonToolbar, FormsModule, ReactiveFormsModule]
})
export class LoginPage implements OnInit {
  private readonly formBuilder = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly toastController = inject(ToastController);
  private readonly loadingController = inject(LoadingController);

  loginForm!: FormGroup;
  loading = false;
  returnUrl: string = '/';

  constructor() {
    addIcons({ alertCircleOutline, lockClosed, lockClosedOutline, personOutline });
  }

  ngOnInit() {
    // Initialize form
    this.loginForm = this.formBuilder.group({
      username: ['', [Validators.required]],
      password: ['', [Validators.required]],
      rememberMe: [false]
    });

    // Get return URL from route parameters or default to '/'
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';
  }

  /**
   * Handle form submission
   */
  async onSubmit() {
    if (this.loginForm.invalid) {
      this.markFormGroupTouched(this.loginForm);
      return;
    }

    const { username, password, rememberMe } = this.loginForm.value;

    const loading = await this.loadingController.create({
      message: 'Logging in...',
    });
    await loading.present();

    this.loading = true;

    // Settles once the session is saved and the current user loaded
    const failure = await firstValueFrom(this.authService.login(username, password, rememberMe))
      .then(() => null, (error: Error) => error);

    await loading.dismiss();
    this.loading = false;

    if (failure) {
      const toast = await this.toastController.create({
        message: failure.message || 'Invalid username or password',
        duration: 3000,
        color: 'danger',
        position: 'top'
      });
      await toast.present();
      return;
    }

    const toast = await this.toastController.create({
      message: 'Login successful!',
      duration: 2000,
      color: 'success',
      position: 'top'
    });
    await toast.present();

    // Redirect to return URL or home
    await this.router.navigateByUrl(this.returnUrl);
  }

  /**
   * Navigate to register page
   */
  goToRegister() {
    this.router.navigate(['/register']);
  }

  /**
   * Navigate to forgot password page
   */
  goToForgotPassword() {
    this.router.navigate(['/forgot-password']);
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
    const field = this.loginForm.get(fieldName);

    if (field?.touched && field?.errors) {
      if (field.errors['required']) {
        return `${this.getFieldLabel(fieldName)} is required`;
      }
    }

    return null;
  }

  /**
   * Get user-friendly field label
   */
  private getFieldLabel(fieldName: string): string {
    const labels: { [key: string]: string } = {
      username: 'Username or Email',
      password: 'Password'
    };
    return labels[fieldName] || fieldName;
  }
}
