import { Component } from '@angular/core';
import { IonHeader, IonModal, IonTitle, IonToolbar } from '@ionic/angular/standalone';

@Component({
    selector: 'app-transformation-modal',
    templateUrl: './transformation-modal.component.html',
    imports: [IonHeader, IonModal, IonTitle, IonToolbar]
})
export class TransformationModalComponent {

  constructor() { }

}
