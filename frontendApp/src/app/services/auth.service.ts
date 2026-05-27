import { Injectable, Injector } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import {
  User,
  Token,
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  ChangePasswordRequest,
  UserUpdate
} from '../models/auth.models';
import { TokenService } from './token.service';
import { BaseService } from './base.service.service';

/**
 * Authentication Service
 * Handles all authentication-related operations
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser$: Observable<User | null>;
  private refreshTokenPromise: Promise<string | null> | null = null;
  private tokenRefreshIntervalId: ReturnType<typeof setInterval> | null = null;

  constructor(
    private http: HttpClient,
    private tokenService: TokenService,
    private baseService: BaseService,
    private router: Router,
    private injector: Injector
  ) {
    this.currentUserSubject = new BehaviorSubject<User | null>(null);
    this.currentUser$ = this.currentUserSubject.asObservable();
  }

  /**
   * Get current user value
   */
  get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Login user
   */
  login(username: string, password: string, rememberMe: boolean = false): Observable<Token> {
    const loginRequest: LoginRequest = { username, password };

    return this.http.post<Token>(`${this.baseService.urlBack}/auth/login`, loginRequest)
      .pipe(
        tap(async (token) => {
          // Save tokens
          await this.tokenService.saveTokens(token.access_token, token.refresh_token, rememberMe);

          // Load user info
          await this.loadCurrentUser();

          // Load user's datasets and workflows after successful login
          await this.loadUserData();
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Load user data (datasets, workflows) after authentication
   */
  private async loadUserData(): Promise<void> {
    try {
      // Lazy injection to avoid circular dependency
      const { DatasetService } = await import('./dataset.service');
      const { WorkflowService } = await import('./worflow.service');

      const datasetService = this.injector.get(DatasetService);
      const workflowService = this.injector.get(WorkflowService);

      // Reload datasets and workflows with authentication
      datasetService.get();
      workflowService.getWorkflows().subscribe();
    } catch (error) {
      console.warn('Failed to load user data:', error);
    }
  }

  /**
   * Register new user
   */
  register(registerData: RegisterRequest): Observable<User> {
    return this.http.post<User>(`${this.baseService.urlBack}/auth/register`, registerData)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    this.stopTokenRefreshTimer();

    // Clear tokens
    await this.tokenService.clearTokens();

    // Clear user state
    this.currentUserSubject.next(null);

    // Clear cached data from services (lazy injection to avoid circular dependency)
    try {
      const { DatasetService } = await import('./dataset.service');
      const { WorkflowService } = await import('./worflow.service');

      const datasetService = this.injector.get(DatasetService);
      const workflowService = this.injector.get(WorkflowService);

      datasetService.clearDatasets();
      workflowService.clearWorkflows();
    } catch (error) {
      console.warn('Failed to clear service caches:', error);
    }

    // Navigate to login page
    this.router.navigate(['/login'], { replaceUrl: true });
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string | null> {
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise;
    }

    this.refreshTokenPromise = this.performRefreshToken();
    return this.refreshTokenPromise;
  }

  private async performRefreshToken(): Promise<string | null> {
    try {
      const refreshToken = await this.tokenService.getRefreshToken();

      if (!refreshToken) {
        return null;
      }

      const token = await this.http.post<Token>(`${this.baseService.urlBack}/auth/refresh`, {
        refresh_token: refreshToken
      }).toPromise();

      if (token) {
        const rememberMe = await this.tokenService.isRememberMe();
        await this.tokenService.saveTokens(token.access_token, token.refresh_token, rememberMe);
        return token.access_token;
      }

      return null;
    } catch (error) {
      console.error('Token refresh failed:', error);
      await this.logout();
      return null;
    } finally {
      this.refreshTokenPromise = null;
    }
  }

  /**
   * Load current user info
   */
  async loadCurrentUser(): Promise<void> {
    try {
      const accessToken = this.tokenService.getAccessToken();

      if (!accessToken) {
        this.currentUserSubject.next(null);
        return;
      }

      const headers = new HttpHeaders({
        'Authorization': `Bearer ${accessToken}`
      });

      const user = await this.http.get<User>(`${this.baseService.urlBack}/auth/me`, { headers }).toPromise();

      if (user) {
        this.currentUserSubject.next(user);

        // Load user data after successfully loading user info
        await this.loadUserData();
      }
    } catch (error) {
      console.error('Failed to load current user:', error);
      this.currentUserSubject.next(null);
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const hasTokens = await this.tokenService.hasTokens();

    if (!hasTokens) {
      return false;
    }

    // Try to refresh token if needed
    const accessToken = this.tokenService.getAccessToken();
    if (!accessToken || this.tokenService.isTokenExpired(accessToken)) {
      const newToken = await this.refreshToken();
      return !!newToken;
    }

    return true;
  }

  /**
   * Check if user is admin
   */
  isAdmin(): boolean {
    const user = this.currentUserValue;
    return user?.role === 'admin';
  }

  /**
   * Forgot password - Send reset email
   */
  forgotPassword(email: string): Observable<{ message: string }> {
    const request: ForgotPasswordRequest = { email };

    return this.http.post<{ message: string }>(`${this.baseService.urlBack}/auth/forgot-password`, request)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Reset password with token
   */
  resetPassword(token: string, newPassword: string): Observable<{ message: string }> {
    const request: ResetPasswordRequest = { token, new_password: newPassword };

    return this.http.post<{ message: string }>(`${this.baseService.urlBack}/auth/reset-password`, request)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Change password (authenticated user)
   */
  changePassword(currentPassword: string, newPassword: string): Observable<{ message: string }> {
    const request: ChangePasswordRequest = { current_password: currentPassword, new_password: newPassword };
    const accessToken = this.tokenService.getAccessToken();

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`
    });

    return this.http.post<{ message: string }>(`${this.baseService.urlBack}/auth/change-password`, request, { headers })
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Update current user profile
   */
  updateProfile(userData: UserUpdate): Observable<User> {
    const accessToken = this.tokenService.getAccessToken();

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${accessToken}`
    });

    return this.http.put<User>(`${this.baseService.urlBack}/auth/me`, userData, { headers })
      .pipe(
        tap((user) => {
          this.currentUserSubject.next(user);
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Auto-refresh token timer
   * Call this on app initialization
   */
  startTokenRefreshTimer(): void {
    if (this.tokenRefreshIntervalId !== null) {
      return;
    }

    // Check every minute if token needs refresh
    this.tokenRefreshIntervalId = setInterval(async () => {
      if (this.tokenService.shouldRefreshToken()) {
        await this.refreshToken();
      }
    }, 60000); // 1 minute
  }

  stopTokenRefreshTimer(): void {
    if (this.tokenRefreshIntervalId !== null) {
      clearInterval(this.tokenRefreshIntervalId);
      this.tokenRefreshIntervalId = null;
    }
  }

  // ==================== ADMIN METHODS ====================

  /**
   * Get all users (Admin only)
   */
  getAllUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${this.baseService.urlBack}/auth/users`)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Get user by ID (Admin only)
   */
  getUserById(userId: string): Observable<User> {
    return this.http.get<User>(`${this.baseService.urlBack}/auth/users/${userId}`)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Delete user (Admin only)
   */
  deleteUser(userId: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseService.urlBack}/auth/users/${userId}`)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Deactivate user (Admin only)
   */
  deactivateUser(userId: string, reason?: string): Observable<any> {
    const body = reason ? { reason } : {};
    return this.http.post(`${this.baseService.urlBack}/auth/users/${userId}/deactivate`, body)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Activate user (Admin only)
   */
  activateUser(userId: string): Observable<any> {
    return this.http.post(`${this.baseService.urlBack}/auth/users/${userId}/activate`, {})
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Update user (Admin only)
   * Can update any field including password
   */
  updateUser(userId: string, userData: UserUpdate): Observable<User> {
    return this.http.put<User>(`${this.baseService.urlBack}/auth/users/${userId}`, userData)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: any): Observable<never> {
    let errorMessage = 'An error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = error.error?.detail || error.message || 'Server error';
    }

    console.error('Auth Service Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
