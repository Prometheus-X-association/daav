import { ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output, Pipe, PipeTransform } from '@angular/core';
import { Data } from '@angular/router';
import { OverlayEventDetail } from '@ionic/core';
import { ClassicPreset } from 'rete';
import { ColumnMapping, DatasetMapper } from 'src/app/models/data-mapper-types';


export class DataMapperControl extends ClassicPreset.Control {
  public buttonDisabled = false;
  constructor(
    public mappings: ColumnMapping[],
    public datasets : DatasetMapper[] = [],
    public callback?: (event?: CustomEvent<OverlayEventDetail<string>>) => void
  ) {
    super();
  }
}

@Component({
    selector: 'app-data-mapper-widget',
    templateUrl: './data-mapper-widget.component.html',
    styleUrls: ['./data-mapper-widget.component.scss'],
    standalone: false
})
export class DataMapperWidgetComponent{

  @Input() data: DataMapperControl;
  isModalOpen= false;
  cdr: ChangeDetectorRef;
  constructor(cdr: ChangeDetectorRef) {
    this.cdr = cdr;
  }


  onWillDismiss(event: Event) {
    const ev = event as CustomEvent<OverlayEventDetail<string>>;
    this.isModalOpen = false;
    if (this.data.callback) {
      this.data.callback(ev);
    }
  }

  openModal(){
    this.isModalOpen = true;
  }

}
