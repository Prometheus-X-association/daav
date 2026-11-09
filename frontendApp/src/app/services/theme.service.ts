import { Injectable } from '@angular/core';

export interface Theme {
  class: string;
  name: string;
}

/**
 * Theme Service
 * Applies the display theme and font chosen by the user and remembers them
 */
@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  readonly themes: Theme[] = [
    {
      class: "",
      name: "Default theme"
    },
    {
      class: "theme-ptx",
      name: "PTX theme"
    }
  ];

  readonly fonts: string[] = ["poppins", "OpenDyslexic"];

  currentTheme = "";
  currentFont = "";

  private htmlClassList = document.documentElement.classList;

  constructor() {
    this.applyTheme(localStorage.getItem("theme"));
    this.applyFont(localStorage.getItem("font"));
  }

  applyTheme(value: string | null): void {
    this.themes.forEach((theme) => {
      if (theme.class !== "") {
        this.htmlClassList.remove(theme.class);
      }
    });

    if (value) {
      this.htmlClassList.add(value);
    }
    this.currentTheme = value || "";

    localStorage.setItem("theme", this.currentTheme);
  }

  applyFont(value: string | null): void {
    this.fonts.forEach((font) => {
      this.htmlClassList.remove(font);
    });

    if (value) {
      this.htmlClassList.add(value);
    }
    this.currentFont = value || "";

    localStorage.setItem("font", this.currentFont);
  }
}
