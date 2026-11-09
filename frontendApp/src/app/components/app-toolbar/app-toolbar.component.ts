import { Component } from '@angular/core';
import { ThemeService } from '../../services/theme.service';

let nextId = 0;

/**
 * Application toolbar shown on top of the side column of the pages
 * Buttons given as content are displayed before the display settings button
 */
@Component({
    selector: 'app-toolbar',
    templateUrl: './app-toolbar.component.html',
    styleUrls: ['./app-toolbar.component.scss'],
    standalone: false
})
export class AppToolbarComponent {
  // Several pages stay in the DOM with Ionic navigation, ids must be unique
  readonly menuId = `theme-menu-${nextId++}`;
  isMenuOpen = false;

  constructor(public themeService: ThemeService) {}

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
  }
}
