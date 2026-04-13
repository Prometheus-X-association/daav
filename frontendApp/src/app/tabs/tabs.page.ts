import { Component } from '@angular/core';
import { LoadingService } from '../services/loading.service';

@Component({
    selector: 'app-tabs',
    templateUrl: 'tabs.page.html',
    styleUrls: ['tabs.page.scss'],
    providers: [
        LoadingService
    ],
    standalone: false
})
export class TabsPage {
  constructor() {
  }

}
