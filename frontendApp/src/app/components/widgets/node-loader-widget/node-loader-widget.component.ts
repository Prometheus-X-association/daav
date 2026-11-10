import { ChangeDetectorRef, Component, Input, OnChanges, SimpleChanges, inject } from '@angular/core';
import { MatSelectChange } from '@angular/material/select';
import { ClassicPreset } from 'rete';
import { IonicModule } from '@ionic/angular';

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
    imports: [IonicModule]
})
export class NodeLoaderWidgetComponent implements OnChanges {
  @Input() data: NodeLoaderControl;
  cdr = inject(ChangeDetectorRef);
  ngOnChanges(changes: SimpleChanges): void {
    this.cdr.detectChanges();
  }
}
