import { ChangeDetectorRef, Component, Input, inject } from "@angular/core";
import { OverlayEventDetail } from "@ionic/core";
import { ClassicPreset } from "rete";
import { DatasetMapper } from "src/app/models/data-mapper-types";
import { IonicModule } from "@ionic/angular";
import { DataFilterComponent } from "../../data-filter/data-filter.component";
import { HasDatasetsPipe } from "../../../models/data-mapper-types";

export class DataFilterControl extends ClassicPreset.Control{
  public buttonDisabled = false;
  public query = {
    condition: 'and',
    rules: []
  };
  
  constructor(
    public datasets: DatasetMapper [] = [],
    public callback?: (event?: CustomEvent<OverlayEventDetail<string>>) => void
  ){
    super();
  }

  public resetQuery() {
    this.query = {
      condition: 'and',
      rules: []
    };
  }
}

@Component({
    selector: 'app-data-filter-widget',
    templateUrl: './data-filter-widget.component.html',
    styleUrls: ['./data-filter-widget.component.scss'],
    imports: [IonicModule, DataFilterComponent, HasDatasetsPipe]
})
export class DataFilterWidgetComponent{
  @Input() data: DataFilterControl;
  isModalOpen = false;
  cdr = inject(ChangeDetectorRef);

  onWillDismiss(event: Event){
    const ev = event as CustomEvent<OverlayEventDetail<string>>;
    this.isModalOpen = false;
    if(this.data.callback){
      this.data.callback(ev);
    }
  }

  openModal(){
    this.isModalOpen = true
  }
}