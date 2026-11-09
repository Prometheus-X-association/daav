import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule, LoadingController, ToastController } from '@ionic/angular';
import { ReactiveFormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { SecuritySectionComponent } from './security-section.component';
import { AuthService } from '../../../services/auth.service';

describe('SecuritySectionComponent', () => {
  let component: SecuritySectionComponent;
  let fixture: ComponentFixture<SecuritySectionComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let toastControllerSpy: jasmine.SpyObj<ToastController>;
  let loadingControllerSpy: jasmine.SpyObj<LoadingController>;

  beforeEach(waitForAsync(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['changePassword']);
    authServiceSpy.changePassword.and.returnValue(of({ message: 'success' } as any));

    const toast = { present: jasmine.createSpy('present') } as any;
    toastControllerSpy = jasmine.createSpyObj('ToastController', ['create']);
    toastControllerSpy.create.and.returnValue(Promise.resolve(toast));

    const loading = { present: jasmine.createSpy('present'), dismiss: jasmine.createSpy('dismiss') } as any;
    loadingControllerSpy = jasmine.createSpyObj('LoadingController', ['create']);
    loadingControllerSpy.create.and.returnValue(Promise.resolve(loading));

    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot(), ReactiveFormsModule],
      declarations: [SecuritySectionComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: ToastController, useValue: toastControllerSpy },
        { provide: LoadingController, useValue: loadingControllerSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(SecuritySectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should not call changePassword when form is invalid', async () => {
    component.changePasswordForm.setValue({ currentPassword: '', newPassword: '', confirmPassword: '' });

    await component.onChangePassword();

    expect(authServiceSpy.changePassword).not.toHaveBeenCalled();
  });

  it('should show a toast when passwords do not match', async () => {
    component.changePasswordForm.setValue({ currentPassword: 'current', newPassword: '12345678', confirmPassword: 'wrongpass' });

    await component.onChangePassword();

    expect(authServiceSpy.changePassword).not.toHaveBeenCalled();
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'New passwords do not match', color: 'danger' }));
  });

  it('should change password successfully and reset the form', async () => {
    component.changePasswordForm.setValue({ currentPassword: 'current', newPassword: '12345678', confirmPassword: '12345678' });

    await component.onChangePassword();

    expect(loadingControllerSpy.create).toHaveBeenCalled();
    expect(authServiceSpy.changePassword).toHaveBeenCalledWith('current', '12345678');
    expect(component.changePasswordForm.value).toEqual({ currentPassword: null, newPassword: null, confirmPassword: null });
  });

  it('should show error toast when changePassword errors', async () => {
    authServiceSpy.changePassword.and.returnValue(throwError(() => new Error('bad')));
    component.changePasswordForm.setValue({ currentPassword: 'current', newPassword: '12345678', confirmPassword: '12345678' });

    await component.onChangePassword();

    expect(component.loading).toBeFalse();
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'bad', color: 'danger' }));
  });
});
