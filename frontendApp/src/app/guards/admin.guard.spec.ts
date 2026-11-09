import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, UrlTree } from '@angular/router';
import { adminGuard } from './admin.guard';
import { AuthService } from '../services/auth.service';

describe('adminGuard', () => {
  let isAdmin: boolean;

  const runGuard = () => TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any));

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { isAdmin: () => isAdmin } }
      ]
    });
  });

  it('should let administrators through', () => {
    isAdmin = true;

    expect(runGuard()).toBeTrue();
  });

  it('should redirect the other users to the account page', () => {
    isAdmin = false;

    const result = runGuard() as UrlTree;

    expect(TestBed.inject(Router).serializeUrl(result)).toBe('/account');
  });
});
