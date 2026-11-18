import { Component, inject } from '@angular/core';
import { ThemeService } from '../../services/theme.service';
import { IonButton, IonButtons, IonIcon, IonTitle, IonToolbar } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { closeOutline, settingsOutline } from 'ionicons/icons';

let nextId = 0;

/**
 * Application toolbar shown in the header of the pages
 * Buttons given as content are displayed next to the title, before the display settings button
 * Content marked with the toolbarEnd attribute is displayed on the right (e.g. the page tabs)
 */
@Component({
    selector: 'app-toolbar',
    templateUrl: './app-toolbar.component.html',
    styleUrls: ['./app-toolbar.component.scss'],
    imports: [IonButton, IonButtons, IonIcon, IonTitle, IonToolbar]
})
export class AppToolbarComponent {
  themeService = inject(ThemeService);

  // Several pages stay in the DOM with Ionic navigation, ids must be unique
  readonly menuId = `theme-menu-${nextId++}`;
  isMenuOpen = false;

  constructor() {
    addIcons({ closeOutline, settingsOutline });
  }

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
  }
}
