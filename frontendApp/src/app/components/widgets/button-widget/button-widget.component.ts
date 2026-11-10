import { ChangeDetectorRef, Component, Input } from '@angular/core';
import { ClassicPreset } from 'rete';
import { MatIconButton } from '@angular/material/button';
import { NgClass } from '@angular/common';
import { MatIcon } from '@angular/material/icon';

export class ButtonControl extends ClassicPreset.Control {
  constructor(
    public onClick: () => void,
    public label?: string,
    public icon?: string,
    public className?: string,
    public disabled?: boolean,
    // Accessible name, required when the button only shows an icon
    public ariaLabel?: string
  ) {
    super();
  }
}

@Component({
    selector: 'app-button-widget',
    templateUrl: './button-widget.component.html',
    styleUrls: ['./button-widget.component.scss'],
    imports: [MatIconButton, NgClass, MatIcon]
})
export class ButtonWidgetComponent  {
  @Input() data: ButtonControl;
  cdr: ChangeDetectorRef;
  constructor(cdr: ChangeDetectorRef) {}
}
