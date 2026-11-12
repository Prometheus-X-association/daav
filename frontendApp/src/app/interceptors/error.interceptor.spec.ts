import { TestBed, fakeAsync, flush } from '@angular/core/testing';
import { HttpErrorResponse, HttpHandler, HttpRequest } from '@angular/common/http';
import { Router } from '@angular/router';
import { ToastController } from '@ionic/angular/standalone';
import { throwError } from 'rxjs';
import { ErrorInterceptor } from './error.interceptor';
import { AuthService } from '../services/auth.service';

describe('ErrorInterceptor', () => {
  let interceptor: ErrorInterceptor;
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;
  let toastController: jasmine.SpyObj<ToastController>;
  let toast: { present: jasmine.Spy };

  const request = new HttpRequest('GET', '/datasets');
  const unauthorized: HttpHandler = {
    handle: () => throwError(() => new HttpErrorResponse({ status: 401, url: '/datasets' }))
  };

  beforeEach(() => {
    authService = jasmine.createSpyObj('AuthService', ['refreshToken', 'logout']);
    authService.refreshToken.and.resolveTo(null);
    authService.logout.and.resolveTo();
    router = jasmine.createSpyObj('Router', ['navigate'], { url: '/workflows' });
    router.navigate.and.resolveTo(true);
    toast = { present: jasmine.createSpy('present').and.resolveTo() };
    toastController = jasmine.createSpyObj('ToastController', ['create']);
    toastController.create.and.resolveTo(toast as any);

    TestBed.configureTestingModule({
      providers: [
        ErrorInterceptor,
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router },
        { provide: ToastController, useValue: toastController },
      ]
    });
    interceptor = TestBed.inject(ErrorInterceptor);
  });

  function intercept(): { error?: any } {
    const result: { error?: any } = {};
    interceptor.intercept(request, unauthorized).subscribe({ error: (error) => result.error = error });
    flush();
    return result;
  }

  function expectRedirectToLogin() {
    expect(router.navigate).toHaveBeenCalledWith(['/login'], { queryParams: { returnUrl: '/workflows' } });
  }

  it('should redirect to the login page when the session cannot be refreshed', fakeAsync(() => {
    const result = intercept();

    expect(authService.logout).toHaveBeenCalled();
    expect(toast.present).toHaveBeenCalled();
    expectRedirectToLogin();
    expect(result.error.message).toBe('Session expired');
  }));

  it('should redirect to the login page when the refresh fails', fakeAsync(() => {
    const failure = new Error('network');
    authService.refreshToken.and.rejectWith(failure);

    const result = intercept();

    expectRedirectToLogin();
    expect(result.error).toBe(failure);
  }));

  it('should still redirect to the login page when the logout fails', fakeAsync(() => {
    authService.logout.and.rejectWith(new Error('storage unavailable'));
    spyOn(console, 'error');

    intercept();

    expect(toast.present).toHaveBeenCalled();
    expectRedirectToLogin();
  }));

  it('should still redirect to the login page when the message cannot be shown', fakeAsync(() => {
    toastController.create.and.rejectWith(new Error('no toast'));
    spyOn(console, 'error');

    intercept();

    expectRedirectToLogin();
  }));

  it('should not try to refresh the session on the login request', fakeAsync(() => {
    const login = new HttpRequest('POST', '/auth/login', {});
    let error: any;
    interceptor.intercept(login, unauthorized).subscribe({ error: (e) => error = e });
    flush();

    expect(authService.refreshToken).not.toHaveBeenCalled();
    expect(error.message).toBe('Unauthorized');
  }));
});
