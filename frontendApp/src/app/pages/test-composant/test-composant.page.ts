import { Component } from '@angular/core';
import { IonContent, IonHeader, IonTitle, IonToolbar } from '@ionic/angular/standalone';
import { DataMapperComponent } from '../../components/data-mapper/data-mapper.component';

@Component({
    selector: 'app-test-composant',
    templateUrl: './test-composant.page.html',
    styleUrls: ['./test-composant.page.scss'],
    imports: [IonContent, IonHeader, IonTitle, IonToolbar, DataMapperComponent]
})
export class TestComposantPage {

  constructor() { }

}
