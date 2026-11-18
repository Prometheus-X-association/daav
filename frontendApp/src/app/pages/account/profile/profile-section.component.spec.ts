import { ComponentFixture, TestBed, fakeAsync, flush, tick, waitForAsync } from '@angular/core/testing';
import { AlertController, LoadingController, ToastController, provideIonicAngular } from '@ionic/angular/standalone';
import { of } from 'rxjs';
import { ProfileSectionComponent } from './profile-section.component';
import { AuthService } from '../../../services/auth.service';

describe('ProfileSectionComponent', () => {
  let component: ProfileSectionComponent;
  let fixture: ComponentFixture<ProfileSectionComponent>;
  let alertControllerSpy: jasmine.SpyObj<AlertController>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let toastControllerSpy: jasmine.SpyObj<ToastController>;
  let loading: { present: jasmine.Spy; dismiss: jasmine.Spy };

  const user = {
    id: 'user-1',
    username: 'jdoe',
    email: 'jdoe@example.org',
    full_name: 'John Doe',
    role: 'user',
    is_active: true,
    created_at: '2025-01-01T00:00:00Z',
    last_login: null
  } as any;

  beforeEach(waitForAsync(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['logout'], { currentUser$: of(user) });
    authServiceSpy.logout.and.returnValue(Promise.resolve());

    const toast = { present: jasmine.createSpy('present').and.returnValue(Promise.resolve()) } as any;
    toastControllerSpy = jasmine.createSpyObj('ToastController', ['create']);
    toastControllerSpy.create.and.returnValue(Promise.resolve(toast));

    loading = { present: jasmine.createSpy('present').and.returnValue(Promise.resolve()), dismiss: jasmine.createSpy('dismiss').and.returnValue(Promise.resolve(true)) };
    const loadingControllerSpy = jasmine.createSpyObj('LoadingController', ['create']);
    loadingControllerSpy.create.and.returnValue(Promise.resolve(loading));

    const alert = { present: jasmine.createSpy('present') } as any;
    alertControllerSpy = jasmine.createSpyObj('AlertController', ['create']);
    alertControllerSpy.create.and.returnValue(Promise.resolve(alert));

    TestBed.configureTestingModule({
    imports: [ProfileSectionComponent],
    providers: [
        provideIonicAngular(),
        { provide: AuthService, useValue: authServiceSpy },
        { provide: AlertController, useValue: alertControllerSpy },
        { provide: ToastController, useValue: toastControllerSpy },
        { provide: LoadingController, useValue: loadingControllerSpy }
    ]
}).compileComponents();

    fixture = TestBed.createComponent(ProfileSectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should display the current user', () => {
    const text = fixture.nativeElement.textContent;

    expect(component.user).toBe(user);
    expect(text).toContain('John Doe');
    expect(text).toContain('jdoe@example.org');
  });

  it('should format null dates as Never', () => {
    expect(component.getFormattedDate(null)).toBe('Never');
  });

  it('should ask for a confirmation before deactivating the account', async () => {
    await component.onDeactivateAccount();

    expect(alertControllerSpy.create).toHaveBeenCalled();
  });

  const deactivateButton = async () => {
    await component.onDeactivateAccount();
    const options = alertControllerSpy.create.calls.mostRecent().args[0];
    return (options.buttons as any[]).find(button => button.role === 'destructive');
  };

  it('should keep the dialog open and warn when the confirmation is wrong', fakeAsync(() => {
    let button: any;
    deactivateButton().then(found => button = found);
    flush();

    expect(button.handler({ confirmation: 'nope' })).toBeFalse();
    flush();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ color: 'warning' }));
    expect(authServiceSpy.logout).not.toHaveBeenCalled();
  }));

  it('should logout once the loading is dismissed after a confirmed deactivation', fakeAsync(() => {
    let button: any;
    deactivateButton().then(found => button = found);
    flush();

    expect(button.handler({ confirmation: 'DEACTIVATE' })).toBeTrue();
    tick(999);
    expect(loading.dismiss).not.toHaveBeenCalled();
    expect(authServiceSpy.logout).not.toHaveBeenCalled();

    tick(1);
    flush();
    expect(loading.dismiss).toHaveBeenCalled();
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'Account deactivated successfully', color: 'success' }));
    expect(authServiceSpy.logout).toHaveBeenCalled();
  }));

  it('should log a failed deactivation instead of leaving the rejection unhandled', fakeAsync(() => {
    const failure = new Error('Storage unavailable');
    authServiceSpy.logout.and.callFake(() => Promise.reject(failure));
    const consoleError = spyOn(console, 'error');
    let button: any;
    deactivateButton().then(found => button = found);
    flush();

    button.handler({ confirmation: 'DEACTIVATE' });
    tick(1000);
    flush();

    expect(consoleError).toHaveBeenCalledWith('Failed to deactivate the account:', failure);
  }));
});
