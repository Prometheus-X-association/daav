import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { ReactiveFormsModule } from '@angular/forms';
import { of } from 'rxjs';
import { UserProfileComponent } from './user-profile.component';
import { AuthService } from '../../services/auth.service';
import { ToastController } from '@ionic/angular';
import { LoadingController } from '@ionic/angular';
import { AlertController } from '@ionic/angular';
import { ModalController } from '@ionic/angular';
import { Router } from '@angular/router';

describe('UserProfileComponent', () => {
  let component: UserProfileComponent;
  let fixture: ComponentFixture<UserProfileComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let toastControllerSpy: jasmine.SpyObj<ToastController>;
  let loadingControllerSpy: jasmine.SpyObj<LoadingController>;
  let alertControllerSpy: jasmine.SpyObj<AlertController>;
  let modalControllerSpy: jasmine.SpyObj<ModalController>;

  beforeEach(waitForAsync(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['changePassword', 'logout'], { currentUser$: of({ id: 'user-1', name: 'Test User' } as any) });
    authServiceSpy.changePassword.and.returnValue(of({ message: 'success' } as any));

    const toast = { present: jasmine.createSpy('present') } as any;
    toastControllerSpy = jasmine.createSpyObj('ToastController', ['create']);
    toastControllerSpy.create.and.returnValue(Promise.resolve(toast));

    const loading = { present: jasmine.createSpy('present'), dismiss: jasmine.createSpy('dismiss') } as any;
    loadingControllerSpy = jasmine.createSpyObj('LoadingController', ['create']);
    loadingControllerSpy.create.and.returnValue(Promise.resolve(loading));

    const alert = { present: jasmine.createSpy('present') } as any;
    alertControllerSpy = jasmine.createSpyObj('AlertController', ['create']);
    alertControllerSpy.create.and.returnValue(Promise.resolve(alert));

    modalControllerSpy = jasmine.createSpyObj('ModalController', ['dismiss']);

    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot(), ReactiveFormsModule],
      declarations: [UserProfileComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: ToastController, useValue: toastControllerSpy },
        { provide: LoadingController, useValue: loadingControllerSpy },
        { provide: AlertController, useValue: alertControllerSpy },
        { provide: ModalController, useValue: modalControllerSpy },
        { provide: Router, useValue: { navigate: jasmine.createSpy('navigate') } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UserProfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should toggle change password form visibility and reset when closed', () => {
    component.showChangePassword = true;
    const resetSpy = spyOn(component.changePasswordForm, 'reset');

    component.toggleChangePassword();

    expect(component.showChangePassword).toBeFalse();
    expect(resetSpy).toHaveBeenCalled();
  });

  it('should not call changePassword when form is invalid', async () => {
    component.changePasswordForm.setValue({ currentPassword: '', newPassword: '', confirmPassword: '' });

    await component.onChangePassword();

    expect(authServiceSpy.changePassword).not.toHaveBeenCalled();
  });

  it('should show a toast when passwords do not match', async () => {
    component.changePasswordForm.setValue({ currentPassword: 'current', newPassword: '12345678', confirmPassword: 'wrongpass' });

    await component.onChangePassword();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'New passwords do not match', duration: 3000, color: 'danger', position: 'top' }));
  });

  it('should change password successfully and reset state', async () => {
    component.changePasswordForm.setValue({ currentPassword: 'current', newPassword: '12345678', confirmPassword: '12345678' });

    await component.onChangePassword();

    expect(loadingControllerSpy.create).toHaveBeenCalled();
    expect(authServiceSpy.changePassword).toHaveBeenCalledWith('current', '12345678');
    expect(component.showChangePassword).toBeFalse();
  });

  it('should show logout confirmation alert', async () => {
    const alert = { present: jasmine.createSpy('present') } as any;
    alertControllerSpy.create.and.returnValue(Promise.resolve(alert));

    await component.onLogout();

    expect(alertControllerSpy.create).toHaveBeenCalled();
    expect(alert.present).toHaveBeenCalled();
  });

  it('should dismiss the modal when dismiss is called', () => {
    component.dismiss();

    expect(modalControllerSpy.dismiss).toHaveBeenCalled();
  });
});
