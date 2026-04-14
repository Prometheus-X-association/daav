import { ChangeDetectorRef, Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { MatSelectChange } from '@angular/material/select';
import { ClassicPreset } from 'rete';
import { selectControlI } from '../select-widget/select-widget.component';
import { OnChange } from 'rete-render-utils/_types/sockets-position/types';

export class NodeLoaderControl extends ClassicPreset.Control {
  loading = false;
  callback?: (event?: MatSelectChange) => void;
  constructor() {
    super();
  }
}

@Component({
    selector: 'app-node-loader-widget',
    templateUrl: './node-loader-widget.component.html',
    styleUrls: ['./node-loader-widget.component.scss'],
    standalone: false
})
export class NodeLoaderWidgetComponent implements OnChanges {
  @Input() data: NodeLoaderControl;
  cdr: ChangeDetectorRef;
  constructor(cdr: ChangeDetectorRef) {
    this.cdr = cdr;
  }
  ngOnChanges(changes: SimpleChanges): void {
    this.cdr.detectChanges();
  }
}
