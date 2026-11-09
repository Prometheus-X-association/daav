import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { AlertController, IonicModule, LoadingController, ToastController } from '@ionic/angular';
import { of } from 'rxjs';
import { ProfileSectionComponent } from './profile-section.component';
import { AuthService } from '../../../services/auth.service';

describe('ProfileSectionComponent', () => {
  let component: ProfileSectionComponent;
  let fixture: ComponentFixture<ProfileSectionComponent>;
  let alertControllerSpy: jasmine.SpyObj<AlertController>;

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
    const authServiceSpy = jasmine.createSpyObj('AuthService', ['logout'], { currentUser$: of(user) });

    const alert = { present: jasmine.createSpy('present') } as any;
    alertControllerSpy = jasmine.createSpyObj('AlertController', ['create']);
    alertControllerSpy.create.and.returnValue(Promise.resolve(alert));

    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot()],
      declarations: [ProfileSectionComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: AlertController, useValue: alertControllerSpy },
        { provide: ToastController, useValue: jasmine.createSpyObj('ToastController', ['create']) },
        { provide: LoadingController, useValue: jasmine.createSpyObj('LoadingController', ['create']) }
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
});
