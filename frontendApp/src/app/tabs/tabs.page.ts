import { Component } from '@angular/core';
import { LoadingService } from '../services/loading.service';
import { IonTabs } from '@ionic/angular/standalone';
import { LoadingComponent } from '../components/main/loading/loading.component';

@Component({
    selector: 'app-tabs',
    templateUrl: 'tabs.page.html',
    styleUrls: ['tabs.page.scss'],
    providers: [
        LoadingService
    ],
    imports: [IonTabs, LoadingComponent]
})
export class TabsPage {
  constructor() {
  }

}
