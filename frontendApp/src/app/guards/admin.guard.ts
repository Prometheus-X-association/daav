import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Admin Guard
 * Protects the administration routes, to be used under the AuthGuard
 * Redirects to the account page when the user is not an administrator
 */
export const adminGuard: CanActivateFn = () => {
  return inject(AuthService).isAdmin() || inject(Router).createUrlTree(['/account']);
};
