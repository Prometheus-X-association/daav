import { TestBed } from '@angular/core/testing';
import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  let service: ThemeService;
  const classList = document.documentElement.classList;

  beforeEach(() => {
    service = TestBed.inject(ThemeService);
  });

  afterEach(() => {
    service.applyTheme('');
    service.applyFont('');
  });

  it('should replace the theme class and remember it', () => {
    service.applyTheme('theme-ptx');

    expect(classList).toContain('theme-ptx');
    expect(service.currentTheme).toBe('theme-ptx');
    expect(localStorage.getItem('theme')).toBe('theme-ptx');

    service.applyTheme('');

    expect(classList).not.toContain('theme-ptx');
    expect(localStorage.getItem('theme')).toBe('');
  });

  it('should replace the font class and remember it', () => {
    service.applyFont('poppins');
    service.applyFont('OpenDyslexic');

    expect(classList).not.toContain('poppins');
    expect(classList).toContain('OpenDyslexic');
    expect(localStorage.getItem('font')).toBe('OpenDyslexic');
  });
});
