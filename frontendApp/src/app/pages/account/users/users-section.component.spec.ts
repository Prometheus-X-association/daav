import { ComponentFixture, TestBed, fakeAsync, flush, waitForAsync } from '@angular/core/testing';
import { AlertController, IonicModule, ToastController } from '@ionic/angular';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { UsersSectionComponent } from './users-section.component';
import { AuthService } from '../../../services/auth.service';

describe('UsersSectionComponent', () => {
  let component: UsersSectionComponent;
  let fixture: ComponentFixture<UsersSectionComponent>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let toastControllerSpy: jasmine.SpyObj<ToastController>;
  let alertControllerSpy: jasmine.SpyObj<AlertController>;
  let router: { navigate: jasmine.Spy };

  const users = [
    { id: 'user-1', username: 'admin', role: 'admin', is_active: true, created_at: '2025-01-01T00:00:00Z', last_login: null },
    { id: 'user-2', username: 'jdoe', role: 'user', is_active: true, created_at: '2025-01-01T00:00:00Z', last_login: null }
  ] as any[];

  beforeEach(waitForAsync(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['getAllUsers', 'deactivateUser', 'activateUser', 'deleteUser', 'updateUser'], { currentUserValue: users[0] });
    authServiceSpy.getAllUsers.and.returnValue(of(users));
    authServiceSpy.deleteUser.and.returnValue(of({ message: 'deleted' }));

    const toast = { present: jasmine.createSpy('present') } as any;
    toastControllerSpy = jasmine.createSpyObj('ToastController', ['create']);
    toastControllerSpy.create.and.returnValue(Promise.resolve(toast));

    const alert = { present: jasmine.createSpy('present') } as any;
    alertControllerSpy = jasmine.createSpyObj('AlertController', ['create']);
    alertControllerSpy.create.and.returnValue(Promise.resolve(alert));

    router = { navigate: jasmine.createSpy('navigate') };

    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot()],
      declarations: [UsersSectionComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: ToastController, useValue: toastControllerSpy },
        { provide: AlertController, useValue: alertControllerSpy },
        { provide: Router, useValue: router }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(UsersSectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should load the users on init', () => {
    expect(authServiceSpy.getAllUsers).toHaveBeenCalled();
    expect(component.allUsers).toEqual(users);
    expect(component.loadingUsers).toBeFalse();
  });

  it('should not offer actions on the current user', () => {
    const rows: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('tbody tr'));

    expect(rows[0].querySelectorAll('.actions ion-button').length).toBe(0);
    expect(rows[1].querySelectorAll('.actions ion-button').length).toBe(3);
  });

  it('should handle loadAllUsers error', async () => {
    authServiceSpy.getAllUsers.and.returnValue(throwError(() => new Error('fail')));

    component.loadAllUsers();
    await fixture.whenStable();

    expect(component.loadingUsers).toBeFalse();
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'Failed to load users: fail', color: 'danger' }));
  });

  it('should delete a user once confirmed and reload the users', fakeAsync(() => {
    authServiceSpy.getAllUsers.calls.reset();

    component.deleteUser(users[1]);
    flush();
    const options = alertControllerSpy.create.calls.mostRecent().args[0]!;
    (options.buttons as any[]).find(button => button.role === 'destructive').handler();
    flush();

    expect(authServiceSpy.deleteUser).toHaveBeenCalledWith('user-2');
    expect(authServiceSpy.getAllUsers).toHaveBeenCalled();
  }));

  it('should navigate to the register page to create a user', () => {
    component.createNewUser();

    expect(router.navigate).toHaveBeenCalledWith(['/register']);
  });

  it('should format null dates as Never', () => {
    expect(component.getFormattedDate(null)).toBe('Never');
  });
});
