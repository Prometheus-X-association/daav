// This file is required by karma.conf.js and loads recursively all the .spec and framework files

import 'zone.js/testing';
import { NgModule, provideZoneChangeDetection } from '@angular/core';
import { getTestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting
} from '@angular/platform-browser-dynamic/testing';

// Since Angular 21, TestBed is zoneless by default. The application uses Zone.js
// (provideZoneChangeDetection in main.ts): run the tests with the same change detection.
@NgModule({ providers: [provideZoneChangeDetection()] })
class ZoneChangeDetectionTestingModule {}

// Ionic 8 / Stencil bug: when a watched aria-* attribute (aria-label, aria-pressed...) of a
// lazy-loaded Ionic component such as ion-button changes before its instance is created,
// Stencil's attributeChangedCallback calls the watcher on an undefined instance and throws
// "Cannot read properties of undefined (reading 'onAriaChanged')". It has no effect (the
// instance reads the current attributes when it is created), but in tests, which change
// bindings right after the first render, it randomly fails the running spec. Ignore only
// this error, in the attributeChangedCallback of the Ionic elements.
const defineCustomElement = customElements.define.bind(customElements);
customElements.define = (name: string, constructor: CustomElementConstructor, options?: ElementDefinitionOptions) => {
  const callback = constructor.prototype.attributeChangedCallback;
  if (name.startsWith('ion-') && callback) {
    constructor.prototype.attributeChangedCallback = function (this: HTMLElement, ...args: unknown[]) {
      try {
        return callback.apply(this, args);
      } catch (error) {
        if (!(error instanceof TypeError && error.message.includes("reading 'onAriaChanged'"))) {
          throw error;
        }
      }
    };
  }
  defineCustomElement(name, constructor, options);
};

// First, initialize the Angular testing environment.
getTestBed().initTestEnvironment(
  [BrowserDynamicTestingModule, ZoneChangeDetectionTestingModule],
  platformBrowserDynamicTesting(),
);
