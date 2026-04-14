import { Component, Input } from '@angular/core';
import { MatCheckboxChange } from '@angular/material/checkbox';
import { ClassicPreset } from 'rete';


export interface CheckboxControlI {
  value: boolean;
  label?: string;
}

export class CheckboxControl
  extends ClassicPreset.Control
  implements CheckboxControlI
{
  value: boolean;
  label?: string;
  callback?: (event?: MatCheckboxChange) => void;
  constructor(data: CheckboxControlI,onChange?:(event?: MatCheckboxChange)=>void) {
    super();
    if (data){
      this.label = data.label ? data.label : null;
      this.value = data.value;
      this.callback = onChange;
    }
  }
}



@Component({
    selector: 'app-checkbox-widget',
    templateUrl: './checkbox-widget.component.html',
    styleUrls: ['./checkbox-widget.component.scss'],
    standalone: false
})
export class CheckboxWidgetComponent {
  @Input() data: CheckboxControl;
  constructor() {}



  onInputChange(event: MatCheckboxChange) {
    //console.log('input change', event);
    this.data.value = event.checked
    if (this.data.callback) {
      this.data.callback(event);
    }
  }
}
