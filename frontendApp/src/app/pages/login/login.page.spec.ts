import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { LoadingController, ToastController, provideIonicAngular } from '@ionic/angular/standalone';
import { Subject, throwError } from 'rxjs';
import { LoginPage } from './login.page';
import { AuthService } from '../../services/auth.service';
import { Token } from '../../models/auth.models';

describe('LoginPage', () => {
  let component: LoginPage;
  let fixture: ComponentFixture<LoginPage>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let toastControllerSpy: jasmine.SpyObj<ToastController>;
  let loading: { present: jasmine.Spy; dismiss: jasmine.Spy };
  let router: { navigate: jasmine.Spy; navigateByUrl: jasmine.Spy };

  const token: Token = { access_token: 'access', refresh_token: 'refresh', token_type: 'bearer' };

  beforeEach(waitForAsync(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['login']);

    const toast = { present: jasmine.createSpy('present').and.returnValue(Promise.resolve()) } as any;
    toastControllerSpy = jasmine.createSpyObj('ToastController', ['create']);
    toastControllerSpy.create.and.returnValue(Promise.resolve(toast));

    loading = {
      present: jasmine.createSpy('present').and.returnValue(Promise.resolve()),
      dismiss: jasmine.createSpy('dismiss').and.returnValue(Promise.resolve(true))
    };
    const loadingControllerSpy = jasmine.createSpyObj('LoadingController', ['create']);
    loadingControllerSpy.create.and.returnValue(Promise.resolve(loading));

    router = {
      navigate: jasmine.createSpy('navigate').and.returnValue(Promise.resolve(true)),
      navigateByUrl: jasmine.createSpy('navigateByUrl').and.returnValue(Promise.resolve(true))
    };

    TestBed.configureTestingModule({
      imports: [LoginPage],
      providers: [
        provideIonicAngular(),
        { provide: AuthService, useValue: authServiceSpy },
        { provide: ToastController, useValue: toastControllerSpy },
        { provide: LoadingController, useValue: loadingControllerSpy },
        { provide: Router, useValue: router },
        { provide: ActivatedRoute, useValue: { snapshot: { queryParams: { returnUrl: '/account/profile' } } } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LoginPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should not login when the form is invalid', async () => {
    await component.onSubmit();

    expect(authServiceSpy.login).not.toHaveBeenCalled();
  });

  it('should redirect to the return URL only once the login has completed', async () => {
    const login$ = new Subject<Token>();
    authServiceSpy.login.and.returnValue(login$);
    component.loginForm.setValue({ username: 'jdoe', password: 'secret', rememberMe: true });

    const submitted = component.onSubmit();
    await fixture.whenStable();

    expect(authServiceSpy.login).toHaveBeenCalledWith('jdoe', 'secret', true);
    expect(loading.dismiss).not.toHaveBeenCalled();
    expect(router.navigateByUrl).not.toHaveBeenCalled();

    login$.next(token);
    login$.complete();
    await submitted;

    expect(loading.dismiss).toHaveBeenCalled();
    expect(component.loading).toBeFalse();
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'Login successful!', color: 'success' }));
    expect(router.navigateByUrl).toHaveBeenCalledWith('/account/profile');
  });

  it('should show the error and stay on the page when the login fails', async () => {
    authServiceSpy.login.and.returnValue(throwError(() => new Error('Incorrect username or password')));
    component.loginForm.setValue({ username: 'jdoe', password: 'wrong', rememberMe: false });

    await component.onSubmit();

    expect(loading.dismiss).toHaveBeenCalled();
    expect(component.loading).toBeFalse();
    expect(toastControllerSpy.create).toHaveBeenCalledWith(jasmine.objectContaining({ message: 'Incorrect username or password', color: 'danger' }));
    expect(router.navigateByUrl).not.toHaveBeenCalled();
  });
});
