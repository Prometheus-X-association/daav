import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { LoadingController, ToastController, provideIonicAngular } from '@ionic/angular/standalone';
import { RegisterPage } from './register.page';
import { AuthService } from '../../services/auth.service';

describe('RegisterPage', () => {
  let component: RegisterPage;
  let fixture: ComponentFixture<RegisterPage>;

  beforeEach(waitForAsync(() => {
    const authServiceSpy = jasmine.createSpyObj('AuthService', ['register', 'isAuthenticated', 'loadCurrentUser']);
    authServiceSpy.isAuthenticated.and.returnValue(Promise.resolve(false));

    TestBed.configureTestingModule({
      imports: [RegisterPage],
      providers: [
        provideIonicAngular(),
        { provide: AuthService, useValue: authServiceSpy },
        { provide: ToastController, useValue: jasmine.createSpyObj('ToastController', ['create']) },
        { provide: LoadingController, useValue: jasmine.createSpyObj('LoadingController', ['create']) },
        provideRouter([])
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RegisterPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  function touch(fieldName: string, value: string): void {
    const field = component.registerForm.get(fieldName)!;
    field.setValue(value);
    field.markAsTouched();
  }

  describe('getFieldError', () => {
    it('should return null for a field that is not touched', () => {
      component.registerForm.get('username')!.setValue('');

      expect(component.getFieldError('username')).toBeNull();
    });

    it('should report a required field', () => {
      touch('firstName', '');

      expect(component.getFieldError('firstName')).toBe('First Name is required');
    });

    it('should report a too short value', () => {
      touch('username', 'ab');

      expect(component.getFieldError('username')).toBe('Username must be at least 3 characters');
    });

    it('should report a too long value', () => {
      touch('username', 'a'.repeat(51));

      expect(component.getFieldError('username')).toBe('Username must not exceed 50 characters');
    });

    it('should report an invalid email', () => {
      touch('email', 'not-an-email');

      expect(component.getFieldError('email')).toBe('Please enter a valid email address');
    });

    it('should report an invalid username pattern', () => {
      touch('username', 'john doe');

      expect(component.getFieldError('username')).toBe(
        'Username can only contain letters, numbers, hyphens, and underscores'
      );
    });

    it('should report a weak password', () => {
      touch('password', 'abcdefgh');

      expect(component.getFieldError('password')).toBe('Password must meet strength requirements');
    });

    it('should report the first error in order', () => {
      touch('username', 'a!');

      expect(component.getFieldError('username')).toBe('Username must be at least 3 characters');

      touch('password', 'abc');

      expect(component.getFieldError('password')).toBe('Password must be at least 8 characters');
    });

    it('should report a password mismatch on the confirmation field', () => {
      component.registerForm.get('password')!.setValue('Secret-123');
      touch('confirmPassword', 'Other-123');

      expect(component.getFieldError('confirmPassword')).toBe('Passwords do not match');
      expect(component.getFieldError('password')).toBeNull();
    });

    it('should report a required confirmation before the mismatch', () => {
      component.registerForm.get('password')!.setValue('Secret-123');
      touch('confirmPassword', '');

      expect(component.getFieldError('confirmPassword')).toBe('Confirm Password is required');
    });

    it('should not report a mismatch on an untouched confirmation field', () => {
      component.registerForm.get('password')!.setValue('Secret-123');
      component.registerForm.get('confirmPassword')!.setValue('Other-123');

      expect(component.getFieldError('confirmPassword')).toBeNull();
    });

    it('should return null for a valid field, an unknown error or an unknown field', () => {
      touch('email', 'john@example.com');

      expect(component.getFieldError('email')).toBeNull();

      const lastName = component.registerForm.get('lastName')!;
      lastName.markAsTouched();
      lastName.setErrors({ custom: true });

      expect(component.getFieldError('lastName')).toBeNull();
      expect(component.getFieldError('unknown')).toBeNull();
    });
  });
});
