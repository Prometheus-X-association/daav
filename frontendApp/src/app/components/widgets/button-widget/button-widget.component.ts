import { ChangeDetectorRef, Component, Input, OnInit } from '@angular/core';
import { ClassicPreset } from 'rete';

export class ButtonControl extends ClassicPreset.Control {
  constructor(
    public onClick: () => void,
    public label?: string,
    public icon?: string,
    public className?: string,
    public disabled?: boolean
  ) {
    super();
  }
}

@Component({
    selector: 'app-button-widget',
    templateUrl: './button-widget.component.html',
    styleUrls: ['./button-widget.component.scss'],
    standalone: false
})
export class ButtonWidgetComponent  {
  @Input() data: ButtonControl;
  cdr: ChangeDetectorRef;
  constructor(cdr: ChangeDetectorRef) {}
}
