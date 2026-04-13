import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { ToastController } from '@ionic/angular';

/**
 * Error Interceptor
 * Handles HTTP errors globally:
 * - 401: Unauthorized - Try to refresh token or redirect to login
 * - 403: Forbidden - Show access denied message
 * - 500: Server error - Show error message
 */
@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  private isRefreshing = false;

  constructor(
    private authService: AuthService,
    private router: Router,
    private toastController: ToastController
  ) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401) {
          return this.handle401Error(request, next);
        }

        if (error.status === 403) {
          this.handle403Error();
        }

        if (error.status >= 500) {
          this.handle500Error(error);
        }

        return throwError(() => error);
      })
    );
  }

  /**
   * Handle 401 Unauthorized errors
   * Try to refresh token, otherwise redirect to login
   */
  private handle401Error(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    // Don't try to refresh on login/register/forgot/reset endpoints
    const skipRefreshUrls = ['/auth/login', '/auth/register', '/auth/forgot-password', '/auth/reset-password'];
    const shouldSkipRefresh = skipRefreshUrls.some(url => request.url.includes(url));

    if (shouldSkipRefresh || this.isRefreshing) {
      return throwError(() => new Error('Unauthorized'));
    }

    this.isRefreshing = true;

    return new Observable(observer => {
      this.authService.refreshToken().then(newToken => {
        this.isRefreshing = false;

        if (newToken) {
          // Retry original request with new token
          const clonedRequest = request.clone({
            setHeaders: {
              Authorization: `Bearer ${newToken}`
            }
          });

          next.handle(clonedRequest).subscribe(
            event => observer.next(event),
            error => observer.error(error),
            () => observer.complete()
          );
        } else {
          // Refresh failed, redirect to login
          this.redirectToLogin();
          observer.error(new Error('Session expired'));
        }
      }).catch(error => {
        this.isRefreshing = false;
        this.redirectToLogin();
        observer.error(error);
      });
    });
  }

  /**
   * Handle 403 Forbidden errors
   */
  private async handle403Error(): Promise<void> {
    const toast = await this.toastController.create({
      message: 'Access denied. You do not have permission to perform this action.',
      duration: 3000,
      color: 'danger',
      position: 'top'
    });
    await toast.present();
  }

  /**
   * Handle 500+ Server errors
   */
  private async handle500Error(error: HttpErrorResponse): Promise<void> {
    const message = error.error?.detail || 'A server error occurred. Please try again later.';

    const toast = await this.toastController.create({
      message,
      duration: 3000,
      color: 'danger',
      position: 'top'
    });
    await toast.present();
  }

  /**
   * Redirect to login page
   */
  private async redirectToLogin(): Promise<void> {
    await this.authService.logout();

    const toast = await this.toastController.create({
      message: 'Your session has expired. Please login again.',
      duration: 3000,
      color: 'warning',
      position: 'top'
    });
    await toast.present();

    this.router.navigate(['/login'], {
      queryParams: { returnUrl: this.router.url }
    });
  }
}
