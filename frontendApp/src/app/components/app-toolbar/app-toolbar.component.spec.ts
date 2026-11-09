import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { AppToolbarComponent } from './app-toolbar.component';
import { ThemeService } from '../../services/theme.service';

describe('AppToolbarComponent', () => {
  let component: AppToolbarComponent;
  let fixture: ComponentFixture<AppToolbarComponent>;
  let themeService: ThemeService;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot()],
      declarations: [AppToolbarComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(AppToolbarComponent);
    component = fixture.componentInstance;
    themeService = TestBed.inject(ThemeService);
    fixture.detectChanges();
  }));

  afterEach(() => {
    themeService.applyTheme('');
    themeService.applyFont('');
  });

  it('should toggle the display settings menu', () => {
    const menu: HTMLElement = fixture.nativeElement.querySelector('.theme-menu');
    expect(menu.classList).not.toContain('is-open');

    component.toggleMenu();
    fixture.detectChanges();

    expect(menu.classList).toContain('is-open');
  });

  it('should give a unique id to the settings menu of each toolbar', () => {
    const other = TestBed.createComponent(AppToolbarComponent).componentInstance;

    expect(other.menuId).not.toBe(component.menuId);
  });

  it('should apply the theme chosen in the menu', () => {
    const themeButtons: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('.theme-btns ion-button'));

    themeButtons[1].click();
    fixture.detectChanges();

    expect(document.documentElement.classList).toContain('theme-ptx');
    expect(themeButtons[1].getAttribute('aria-pressed')).toBe('true');
  });
});
