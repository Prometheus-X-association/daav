import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { AppToolbarComponent } from './app-toolbar.component';
import { ThemeService } from '../../services/theme.service';

describe('AppToolbarComponent', () => {
  let component: AppToolbarComponent;
  let fixture: ComponentFixture<AppToolbarComponent>;
  let themeService: ThemeService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IonicModule.forRoot(), AppToolbarComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(AppToolbarComponent);
    component = fixture.componentInstance;
    themeService = TestBed.inject(ThemeService);
    fixture.detectChanges();

    // Wait for the lazy-loaded Ionic buttons: changing a watched aria-* attribute of an
    // ion-button before its instance exists throws in Stencil ("reading 'onAriaChanged'")
    await customElements.whenDefined('ion-button');
    const buttons = Array.from(fixture.nativeElement.querySelectorAll('ion-button')) as any[];
    await Promise.all(buttons.map((button) => button.componentOnReady()));
  });

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
