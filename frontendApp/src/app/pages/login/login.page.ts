import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { ToastController, LoadingController } from '@ionic/angular';
import { AuthService } from '../../services/auth.service';

@Component({
    selector: 'app-login',
    templateUrl: './login.page.html',
    styleUrls: ['./login.page.scss'],
    standalone: false
})
export class LoginPage implements OnInit {
  loginForm!: FormGroup;
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

    this.authService.login(username, password, rememberMe).subscribe({
      next: async (token) => {
        await loading.dismiss();
        this.loading = false;

        const toast = await this.toastController.create({
          message: 'Login successful!',
          duration: 2000,
          color: 'success',
          position: 'top'
        });
        await toast.present();

        // Redirect to return URL or home
        this.router.navigateByUrl(this.returnUrl);
      },
      error: async (error) => {
        await loading.dismiss();
        this.loading = false;

        const toast = await this.toastController.create({
          message: error.message || 'Invalid username or password',
          duration: 3000,
          color: 'danger',
          position: 'top'
        });
        await toast.present();
      }
    });
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
