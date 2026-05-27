import { ChangeDetectorRef, Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { ClassicPreset } from 'rete';


export interface inputAutoCompleteControlI {
  value: string;
  list: string[];
  readonly?: boolean;
  label?: string;
  type: 'text' | 'number' | 'email' | 'password' | 'search' | 'tel' | 'url' | 'date' | 'datetime-local' | 'month' | 'week' | 'time' | 'color';
  showPassword?: boolean;
  disabled ?: boolean;
}

export class InputAutoCompleteControl
  extends ClassicPreset.Control
  implements inputAutoCompleteControlI
{
  value: string;
  list: string[];
  readonly?: boolean;
  label?: string;
  callback?: (event?: InputEvent | MatAutocompleteSelectedEvent) => void;
  type: 'number' | 'text' | 'email' | 'password' | 'search' | 'tel' | 'url' | 'date' | 'datetime-local' | 'month' | 'week' | 'time' | 'color';
  showPassword: boolean = false;
  disabled: boolean;
  constructor(data: inputAutoCompleteControlI,onChange?:(event?: InputEvent |MatAutocompleteSelectedEvent)=>void) {
    super();
    if (data){
      this.label = data.label ? data.label : null;
      this.readonly = data.readonly ? data.readonly : false;
      this.disabled = data.disabled ? data.disabled : false;
      this.value = data.value;
      this.list = data.list;
      this.type = data.type;
      this.showPassword = data.showPassword || false;
      this.callback = onChange;
    }
  }

  togglePasswordVisibility(){
    this.showPassword = !this.showPassword;
  }
}


@Component({
    selector: 'app-input-auto-complete-widget',
    templateUrl: './input-auto-complete-widget.component.html',
    styleUrls: ['./input-auto-complete-widget.component.scss'],
    standalone: false
})
export class InputAutoCompleteWidgetComponent implements OnInit, OnChanges {

  @Input() data: InputAutoCompleteControl;
  cdr: ChangeDetectorRef;
  filteredOptions: string[];
  constructor(cdr: ChangeDetectorRef) {
    this.cdr = cdr;
  }
  ngOnInit() {
    this.filteredOptions = this.data.list;
  }

  ngOnChanges(changes: SimpleChanges): void {
    this.cdr.detectChanges();
  }

  onInputChange(event: Event) {
    const inputEvent = event as InputEvent;
    console.log('input change', inputEvent);
    this.filteredOptions = this._filter((inputEvent.target as HTMLInputElement).value);
    if (this.data.callback) {
      this.data.callback(inputEvent);
    }
  }
  onCompleteSelectChange(event: MatAutocompleteSelectedEvent) {
    console.log('input change', event);
    if (this.data.callback) {
      this.data.callback(event);
    }
  }

  getInputType(){
    if (this.data.type === 'password' && this.data.showPassword === true) {
      return 'text';
    }
    return this.data.type;
  }

  togglePasswordVisibility(event: Event) {
    this.data.togglePasswordVisibility();
    this.cdr.detectChanges();
  }

  private _filter(value: string): string[] {
    const filterValue = value.toLowerCase();

    return this.data.list.filter(option => option.toLowerCase().includes(filterValue));
  }
}
