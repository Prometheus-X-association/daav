
import { ChangeDetectorRef, Component, Input, inject } from '@angular/core';
import { ClassicPreset } from 'rete';
import { IonModalCustomEvent, OverlayEventDetail } from '@ionic/core';
import { JsonEditorOptions, JsonEditor } from 'ang-jsoneditor';
import { IonButton, IonContent, IonFab, IonFabButton, IonHeader, IonIcon, IonItem, IonLabel, IonModal, IonTitle, IonToolbar } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { add, chevronDownOutline, chevronUpOutline, trashOutline } from 'ionicons/icons';
import { CdkAccordion, CdkAccordionItem } from '@angular/cdk/accordion';
import { FormsModule } from '@angular/forms';

export class JsonInputsControl extends ClassicPreset.Control {
  public buttonDisabled = false;
datasets: any;
mappings: any;
  constructor(
    public inputsDataExample: string[],
    public callback?: (event?: IonModalCustomEvent<OverlayEventDetail<boolean>>) => void
  ) {
    super();
  }
}


@Component({
    selector: 'app-json-inputs-widget',
    templateUrl: './json-inputs-widget.component.html',
    styleUrls: ['./json-inputs-widget.component.scss'],
    imports: [IonButton, IonContent, IonFab, IonFabButton, IonHeader, IonIcon, IonItem, IonLabel, IonModal, IonTitle, IonToolbar, CdkAccordion, CdkAccordionItem, JsonEditor, FormsModule]
})
export class JsonInputsWidgetComponent   {
  @Input() data: JsonInputsControl;
  isModalOpen= false;
  cdr = inject(ChangeDetectorRef);
  hasChanged = false;

  makeOptions = () => {
    let editorOptions = new JsonEditorOptions();
    editorOptions.modes = ['code', 'text', 'tree', 'view'];
    return editorOptions;
  }

  constructor() {
    addIcons({ add, chevronDownOutline, chevronUpOutline, trashOutline });
  }

  onWillDismiss(event: IonModalCustomEvent<OverlayEventDetail<any>>) {
    event.detail.data = this.hasChanged;
    this.isModalOpen = false;
    if (this.data.callback) {
      this.data.callback(event);
    }
  }

  openModal(){

    console.log('Opening modal, inputsDataExample:', this.data?.inputsDataExample);
    this.isModalOpen = true;
    this.hasChanged = false;

    this.cdr.detectChanges();
  }

  addInputExample() {
    if (!this.data.inputsDataExample) {
      this.data.inputsDataExample = [];
    }
    this.data.inputsDataExample.push(null);
    this.hasChanged = true;
  }

  removeInputExample(index: number) {
    if (this.data.inputsDataExample && this.data.inputsDataExample.length > index) {
      this.data.inputsDataExample.splice(index, 1);
      this.hasChanged = true;
    }
  }

  refreshData() {
    this.cdr.detectChanges();
  }

}
