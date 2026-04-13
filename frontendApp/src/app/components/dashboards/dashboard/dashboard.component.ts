import { HttpClient } from '@angular/common/http';
import { Component, inject, Input, OnInit } from '@angular/core';
import { Dataset } from 'src/app/models/dataset';
import { DatasetService } from 'src/app/services/dataset.service';

@Component({
    selector: 'app-dashboard',
    templateUrl: './dashboard.component.html',
    styleUrls: ['./dashboard.component.scss'],
    standalone: false
})

export class DashboardComponent {

  protected http = inject(HttpClient);
  protected datasetService = inject(DatasetService);
  
  @Input() dataset:Dataset;
  constructor() { }

}
