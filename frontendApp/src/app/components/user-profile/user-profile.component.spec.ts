import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { ReactiveFormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
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
    authServiceSpy = jasmine.createSpyObj('AuthService', ['changePassword', 'logout', 'updateUser', 'getAllUsers', 'deactivateUser', 'activateUser', 'deleteUser'], { currentUser$: of({ id: 'user-1', name: 'Test User' } as any) });
    authServiceSpy.changePassword.and.returnValue(of({ message: 'success' } as any));
    authServiceSpy.updateUser.and.returnValue(of({ id: 'user-1', name: 'Test User', config: { credentials: {} } } as any));
    authServiceSpy.getAllUsers.and.returnValue(of([]));
    authServiceSpy.deactivateUser.and.returnValue(of({} as any));
    authServiceSpy.activateUser.and.returnValue(of({} as any));
    authServiceSpy.deleteUser.and.returnValue(of({} as any));

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

  it('should return empty credentials when user has no config', () => {
    component.user = { config: {} } as any;
    expect(component.getCredentials()).toEqual([]);
  });

  it('should start and cancel editing credential', () => {
    component.user = { config: { credentials: { key1: 'value1' } } } as any;
    component.startEditCredential('key1');
    expect(component.editingCredential).toBe('key1');
    expect(component.editCredentialForm.get('credentialValueEdit')?.value).toBe('value1');

    component.cancelEditCredential();
    expect(component.editingCredential).toBeNull();
  });

  it('should add credential successfully', async () => {
    component.user = { id: 'user-1', config: { credentials: {} } } as any;
    component.credentialForm.setValue({ credentialKey: 'newKey', credentialValue: 'newValue' });

    await component.addCredential();

    expect(authServiceSpy.updateUser).toHaveBeenCalledWith('user-1', jasmine.objectContaining({ config: jasmine.objectContaining({ credentials: jasmine.objectContaining({ newKey: 'newValue' }) }) }));
    expect(component.credentialForm.value).toEqual({ credentialKey: null, credentialValue: null });
  });

  it('should not add credential when duplicate key exists', async () => {
    component.user = { id: 'user-1', config: { credentials: { key1: 'value1' } } } as any;
    component.credentialForm.setValue({ credentialKey: 'key1', credentialValue: 'newValue' });

    await component.addCredential();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'Credential key already exists', duration: 3000, color: 'warning', position: 'top' }));
  });

  it('should save edited credential successfully', async () => {
    component.user = { id: 'user-1', config: { credentials: { key1: 'value1' } } } as any;
    component.editingCredential = 'key1';
    component.editCredentialForm.setValue({ credentialValueEdit: 'updatedValue' });

    await component.saveEditedCredential();

    expect(authServiceSpy.updateUser).toHaveBeenCalledWith('user-1', jasmine.objectContaining({ config: jasmine.objectContaining({ credentials: jasmine.objectContaining({ key1: 'updatedValue' }) }) }));
    expect(component.editingCredential).toBeNull();
  });

  it('should not add credential when form is invalid', async () => {
    component.user = { id: 'user-1', config: { credentials: {} } } as any;
    component.credentialForm.setValue({ credentialKey: '', credentialValue: '' });

    await component.addCredential();

    expect(authServiceSpy.updateUser).not.toHaveBeenCalled();
  });

  it('should not add credential when user config is missing', async () => {
    component.user = { id: 'user-1' } as any;
    component.credentialForm.setValue({ credentialKey: 'key2', credentialValue: 'value2' });

    await component.addCredential();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'User config not available', duration: 3000, color: 'danger', position: 'top' }));
  });

  it('should show error toast when changePassword subscription errors', async () => {
    authServiceSpy.changePassword.and.returnValue(throwError(() => new Error('bad')));
    component.changePasswordForm.setValue({ currentPassword: 'current', newPassword: '12345678', confirmPassword: '12345678' });

    await component.onChangePassword();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'bad', duration: 3000, color: 'danger', position: 'top' }));
  });

  it('should not save edited credential when no editing credential exists', async () => {
    component.user = { id: 'user-1', config: { credentials: { key1: 'value1' } } } as any;
    component.editingCredential = null;
    component.editCredentialForm.setValue({ credentialValueEdit: 'updatedValue' });

    await component.saveEditedCredential();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'No credential selected for editing', duration: 3000, color: 'warning', position: 'top' }));
  });

  it('should not save edited credential when user config is missing', async () => {
    component.user = { id: 'user-1' } as any;
    component.editingCredential = 'key1';
    component.editCredentialForm.setValue({ credentialValueEdit: 'updatedValue' });

    await component.saveEditedCredential();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'User config not available', duration: 3000, color: 'danger', position: 'top' }));
  });

  it('should return credentials list when config exists', () => {
    component.user = { config: { credentials: { a: '1', b: '2' } } } as any;
    expect(component.getCredentials()).toEqual([{ key: 'a', value: '1' }, { key: 'b', value: '2' }]);
  });

  it('should track credential by key', () => {
    expect(component.trackByCredentialKey(0, { key: 'a', value: '1' } as any)).toBe('a');
  });

  it('should toggle user management and load users when empty', async () => {
    component.showUserManagement = false;
    component.allUsers = [];

    await component.toggleUserManagement();

    expect(component.showUserManagement).toBeTrue();
    expect(authServiceSpy.getAllUsers).toHaveBeenCalled();
  });

  it('should handle loadAllUsers error', async () => {
    authServiceSpy.getAllUsers.and.returnValue(throwError(() => new Error('fail')));
    component.loadingUsers = false;

    await component.loadAllUsers();

    expect(component.loadingUsers).toBeFalse();
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'Failed to load users: fail', duration: 3000, color: 'danger', position: 'top' }));
  });

  it('should show logout confirmation alert', async () => {
    const alert = { present: jasmine.createSpy('present') } as any;
    alertControllerSpy.create.and.returnValue(Promise.resolve(alert));

    await component.onLogout();

    expect(alertControllerSpy.create).toHaveBeenCalled();
    expect(alert.present).toHaveBeenCalled();
  });

  it('should report admin status correctly', () => {
    component.user = { role: 'admin' } as any;
    expect(component.isAdmin()).toBeTrue();

    component.user = { role: 'user' } as any;
    expect(component.isAdmin()).toBeFalse();
  });

  it('should format null dates as Never', () => {
    expect(component.getFormattedDate(null)).toBe('Never');
  });

  it('should toggle credentials visibility and reset edit form when hiding', () => {
    component.showCredentials = true;
    const resetSpy = spyOn(component.editCredentialForm, 'reset');

    component.toggleCredentials();

    expect(component.showCredentials).toBeFalse();
    expect(resetSpy).toHaveBeenCalled();
  });

  it('should dismiss the modal when dismiss is called', () => {
    component.dismiss();

    expect(modalControllerSpy.dismiss).toHaveBeenCalled();
  });
});
