import { Injectable } from '@angular/core';
import {
  CanActivate,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
  Router,
  UrlTree
} from '@angular/router';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Auth Guard
 * Protects routes that require authentication
 * Redirects to /login if not authenticated, storing the attempted URL
 * Redirects to /change-password while the user must change their password
 */
@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  async canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Promise<boolean | UrlTree> {

    const isAuthenticated = await this.authService.isAuthenticated();

    if (isAuthenticated) {
      // Load user info if not already loaded
      if (!this.authService.currentUserValue) {
        await this.authService.loadCurrentUser();
      }

      const mustChangePassword = !!this.authService.currentUserValue?.must_change_password;
      const isPasswordChangeRoute = !!route.data['passwordChangeRoute'];

      if (mustChangePassword && !isPasswordChangeRoute) {
        return this.router.createUrlTree(['/change-password'], {
          queryParams: { returnUrl: state.url }
        });
      }

      if (!mustChangePassword && isPasswordChangeRoute) {
        return this.router.createUrlTree(['/']);
      }

      return true;
    }

    // Store the attempted URL for redirecting after login
    const returnUrl = state.url;

    // Redirect to login page with return URL
    return this.router.createUrlTree(['/login'], {
      queryParams: { returnUrl }
    });
  }
}
