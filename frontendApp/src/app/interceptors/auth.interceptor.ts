import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TokenService } from '../services/token.service';

/**
 * Auth Interceptor
 * Automatically adds JWT access token to all HTTP requests
 */
@Injectable()
export class AuthInterceptor implements HttpInterceptor {

  constructor(private tokenService: TokenService) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // Get access token
    const accessToken = this.tokenService.getAccessToken();

    // Skip adding token for login/forgot-password/reset-password endpoints
    const skipAuthUrls = ['/auth/login', '/auth/forgot-password', '/auth/reset-password'];
    const shouldSkip = skipAuthUrls.some(url => request.url.includes(url));

    if (accessToken && !shouldSkip) {
      // Clone request and add Authorization header
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${accessToken}`
        }
      });
    }

    return next.handle(request);
  }
}
