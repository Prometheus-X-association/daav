import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { LoadingService } from 'src/app/services/loading.service';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
@Component({
    selector: 'app-loading',
    templateUrl: './loading.component.html',
    styleUrls: ['./loading.component.scss'],
    imports: [CommonModule, MatProgressSpinnerModule]
})
export class LoadingComponent {

  constructor(public loadingService:LoadingService) { }

}
