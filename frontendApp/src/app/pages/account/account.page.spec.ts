import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { AlertController, IonicModule } from '@ionic/angular';
import { provideRouter, Router } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { AccountPage } from './account.page';
import { AuthService } from '../../services/auth.service';
import { User } from '../../models/auth.models';

describe('AccountPage', () => {
  let component: AccountPage;
  let fixture: ComponentFixture<AccountPage>;
  let currentUser$: BehaviorSubject<User | null>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let alertControllerSpy: jasmine.SpyObj<AlertController>;

  beforeEach(waitForAsync(() => {
    currentUser$ = new BehaviorSubject<User | null>({ id: 'user-1', username: 'jdoe', full_name: 'John Doe', role: 'user' } as any);
    authServiceSpy = jasmine.createSpyObj('AuthService', ['logout'], { currentUser$ });

    const alert = { present: jasmine.createSpy('present') } as any;
    alertControllerSpy = jasmine.createSpyObj('AlertController', ['create']);
    alertControllerSpy.create.and.returnValue(Promise.resolve(alert));

    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot()],
      declarations: [AccountPage],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
      providers: [
        provideRouter([{ path: 'account/:section', children: [] }]),
        { provide: AuthService, useValue: authServiceSpy },
        { provide: AlertController, useValue: alertControllerSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AccountPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should only show the users section to administrators', () => {
    expect(component.visibleSections.map(section => section.path)).toEqual(['profile', 'security', 'credentials']);

    currentUser$.next({ id: 'user-1', role: 'admin' } as any);

    expect(component.visibleSections.map(section => section.path)).toContain('users');
  });

  it('should follow the section displayed by the router', async () => {
    await TestBed.inject(Router).navigateByUrl('/account/credentials');

    expect(component.currentSection?.label).toBe('Credentials');
  });

  it('should logout once confirmed', async () => {
    await component.onLogout();
    const options = alertControllerSpy.create.calls.mostRecent().args[0]!;
    (options.buttons as any[]).find(button => button.role === 'destructive').handler();

    expect(authServiceSpy.logout).toHaveBeenCalled();
  });
});
