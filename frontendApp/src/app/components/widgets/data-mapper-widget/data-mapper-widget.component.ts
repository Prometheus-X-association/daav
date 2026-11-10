import { ChangeDetectorRef, Component, Input, inject } from '@angular/core';
import { OverlayEventDetail } from '@ionic/core';
import { ClassicPreset } from 'rete';
import { ColumnMapping, DatasetMapper } from 'src/app/models/data-mapper-types';
import { IonicModule } from '@ionic/angular';
import { DataMapperComponent } from '../../data-mapper/data-mapper.component';
import { HasDatasetsPipe } from '../../../models/data-mapper-types';


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
    imports: [IonicModule, DataMapperComponent, HasDatasetsPipe]
})
export class DataMapperWidgetComponent{

  @Input() data: DataMapperControl;
  isModalOpen= false;
  cdr = inject(ChangeDetectorRef);


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
