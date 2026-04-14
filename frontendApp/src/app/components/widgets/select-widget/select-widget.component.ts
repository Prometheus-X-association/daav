import { ChangeDetectorRef, Component, EventEmitter, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { MatSelectChange } from '@angular/material/select';
import { ClassicPreset } from 'rete';

export interface selectControlI {
  value: string;
  list: { label: string; value: string; default?: boolean, data?: any }[];
  none?: boolean;
  new?: boolean;
  label?: string;
}

export class SelectControl
  extends ClassicPreset.Control
  implements selectControlI
{
  value: string;
  oldValue : string;
  list: { label: string; value: string; default?: boolean , data?: any}[];
  none?: boolean;
  new?: boolean;
  label?: string;
  callback?: (event?: MatSelectChange, source? : SelectWidgetComponent) => void;
  constructor(data: selectControlI,onChange?:(event?: MatSelectChange)=>void) {
    super();
    if (data){
      this.label = data.label ? data.label : null;
      this.none = data.none ? data.none : false;
      this.none = data.new ? data.new : false;
      this.value = data.value;
      this.list = data.list;
      this.callback = onChange;
    }
  }
}

@Component({
    selector: 'app-select-widget',
    templateUrl: './select-widget.component.html',
    styleUrls: ['./select-widget.component.scss'],
    standalone: false
})
export class SelectWidgetComponent implements OnChanges {
  @Input() data: SelectControl;
  cdr: ChangeDetectorRef;
  constructor(cdr: ChangeDetectorRef) {
    this.cdr = cdr;
  }
  ngOnChanges(changes: SimpleChanges): void {
    this.cdr.detectChanges();
  }
  onOpenedChange(event: boolean) {
    if (event) {
      this.data.oldValue = this.data.value;
    }
  }
}
