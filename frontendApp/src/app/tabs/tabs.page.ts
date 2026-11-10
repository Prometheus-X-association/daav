import { Component } from '@angular/core';
import { LoadingService } from '../services/loading.service';
import { IonicModule } from '@ionic/angular';
import { LoadingComponent } from '../components/main/loading/loading.component';

@Component({
    selector: 'app-tabs',
    templateUrl: 'tabs.page.html',
    styleUrls: ['tabs.page.scss'],
    providers: [
        LoadingService
    ],
    imports: [IonicModule, LoadingComponent]
})
export class TabsPage {
  constructor() {
  }

}
