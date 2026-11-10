import { Component } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { DataMapperComponent } from '../../components/data-mapper/data-mapper.component';

@Component({
    selector: 'app-test-composant',
    templateUrl: './test-composant.page.html',
    styleUrls: ['./test-composant.page.scss'],
    imports: [IonicModule, DataMapperComponent]
})
export class TestComposantPage {

  constructor() { }

}
