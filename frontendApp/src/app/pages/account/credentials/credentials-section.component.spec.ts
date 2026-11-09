import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { AlertController, IonicModule, LoadingController, ToastController } from '@ionic/angular';
import { ReactiveFormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { CredentialsSectionComponent } from './credentials-section.component';
import { AuthService } from '../../../services/auth.service';

describe('CredentialsSectionComponent', () => {
  let component: CredentialsSectionComponent;
  let fixture: ComponentFixture<CredentialsSectionComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let toastControllerSpy: jasmine.SpyObj<ToastController>;
  let alertControllerSpy: jasmine.SpyObj<AlertController>;

  beforeEach(waitForAsync(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['updateProfile'], { currentUser$: of({ id: 'user-1', config: { credentials: {} } } as any) });
    authServiceSpy.updateProfile.and.returnValue(of({ id: 'user-1', config: { credentials: {} } } as any));

    const toast = { present: jasmine.createSpy('present') } as any;
    toastControllerSpy = jasmine.createSpyObj('ToastController', ['create']);
    toastControllerSpy.create.and.returnValue(Promise.resolve(toast));

    const loading = { present: jasmine.createSpy('present'), dismiss: jasmine.createSpy('dismiss') } as any;
    const loadingControllerSpy = jasmine.createSpyObj('LoadingController', ['create']);
    loadingControllerSpy.create.and.returnValue(Promise.resolve(loading));

    const alert = { present: jasmine.createSpy('present') } as any;
    alertControllerSpy = jasmine.createSpyObj('AlertController', ['create']);
    alertControllerSpy.create.and.returnValue(Promise.resolve(alert));

    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot(), ReactiveFormsModule],
      declarations: [CredentialsSectionComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: ToastController, useValue: toastControllerSpy },
        { provide: LoadingController, useValue: loadingControllerSpy },
        { provide: AlertController, useValue: alertControllerSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CredentialsSectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should return empty credentials when user has no config', () => {
    component.user = { config: {} } as any;
    expect(component.getCredentials()).toEqual([]);
  });

  it('should return credentials list when config exists', () => {
    component.user = { config: { credentials: { a: '1', b: '2' } } } as any;
    expect(component.getCredentials()).toEqual([{ key: 'a', value: '1' }, { key: 'b', value: '2' }]);
  });

  it('should start and cancel editing credential', () => {
    component.user = { config: { credentials: { key1: 'value1' } } } as any;
    component.startEditCredential('key1');
    expect(component.editingCredential).toBe('key1');
    expect(component.editCredentialForm.get('credentialValueEdit')?.value).toBe('value1');

    component.cancelEditCredential();
    expect(component.editingCredential).toBeNull();
  });

  it('should add credential through the current user profile without mutating the user', async () => {
    const credentials = { key1: 'value1' };
    component.user = { id: 'user-1', config: { credentials } } as any;
    component.credentialForm.setValue({ credentialKey: 'newKey', credentialValue: 'newValue' });

    await component.addCredential();

    expect(authServiceSpy.updateProfile).toHaveBeenCalledWith({ config: jasmine.objectContaining({ credentials: { key1: 'value1', newKey: 'newValue' } }) } as any);
    expect(credentials).toEqual({ key1: 'value1' });
    expect(component.credentialForm.value).toEqual({ credentialKey: null, credentialValue: null });
  });

  it('should keep the form when adding a credential fails', async () => {
    authServiceSpy.updateProfile.and.returnValue(throwError(() => new Error('fail')));
    component.user = { id: 'user-1', config: { credentials: {} } } as any;
    component.credentialForm.setValue({ credentialKey: 'newKey', credentialValue: 'newValue' });

    await component.addCredential();

    expect(component.credentialForm.value).toEqual({ credentialKey: 'newKey', credentialValue: 'newValue' });
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'Failed to add credential: fail', color: 'danger' }));
  });

  it('should not add credential when duplicate key exists', async () => {
    component.user = { id: 'user-1', config: { credentials: { key1: 'value1' } } } as any;
    component.credentialForm.setValue({ credentialKey: 'key1', credentialValue: 'newValue' });

    await component.addCredential();

    expect(authServiceSpy.updateProfile).not.toHaveBeenCalled();
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'Credential key already exists', color: 'warning' }));
  });

  it('should not add credential when form is invalid', async () => {
    component.user = { id: 'user-1', config: { credentials: {} } } as any;
    component.credentialForm.setValue({ credentialKey: '', credentialValue: '' });

    await component.addCredential();

    expect(authServiceSpy.updateProfile).not.toHaveBeenCalled();
  });

  it('should not add credential when user config is missing', async () => {
    component.user = { id: 'user-1' } as any;
    component.credentialForm.setValue({ credentialKey: 'key2', credentialValue: 'value2' });

    await component.addCredential();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'User config not available', color: 'danger' }));
  });

  it('should save edited credential successfully', async () => {
    component.user = { id: 'user-1', config: { credentials: { key1: 'value1' } } } as any;
    component.editingCredential = 'key1';
    component.editCredentialForm.setValue({ credentialValueEdit: 'updatedValue' });

    await component.saveEditedCredential();

    expect(authServiceSpy.updateProfile).toHaveBeenCalledWith({ config: jasmine.objectContaining({ credentials: { key1: 'updatedValue' } }) } as any);
    expect(component.editingCredential).toBeNull();
  });

  it('should not save edited credential when no editing credential exists', async () => {
    component.user = { id: 'user-1', config: { credentials: { key1: 'value1' } } } as any;
    component.editingCredential = null;
    component.editCredentialForm.setValue({ credentialValueEdit: 'updatedValue' });

    await component.saveEditedCredential();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'No credential selected for editing', color: 'warning' }));
  });

  it('should not save edited credential when user config is missing', async () => {
    component.user = { id: 'user-1' } as any;
    component.editingCredential = 'key1';
    component.editCredentialForm.setValue({ credentialValueEdit: 'updatedValue' });

    await component.saveEditedCredential();

    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'User config not available', color: 'danger' }));
  });

  it('should delete credential once confirmed', async () => {
    component.user = { id: 'user-1', config: { credentials: { key1: 'value1', key2: 'value2' } } } as any;

    await component.deleteCredential('key1');
    const options = alertControllerSpy.create.calls.mostRecent().args[0]!;
    const deleteButton = (options.buttons as any[]).find(button => button.role === 'destructive');
    await deleteButton.handler();

    expect(authServiceSpy.updateProfile).toHaveBeenCalledWith({ config: jasmine.objectContaining({ credentials: { key2: 'value2' } }) } as any);
  });
});
