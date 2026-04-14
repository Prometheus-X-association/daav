import { Component, Input, Output, EventEmitter, OnInit, ViewChild, output } from '@angular/core';
// import { Observable } from 'rxjs';
import { Dataset } from 'src/app/models/dataset';
import { DataRenderTypes } from 'src/app/models/data-render-types';
import { DatasetService } from 'src/app/services/dataset.service';
import { DatasetsModalComponent } from '../../datasets-modal/datasets-modal.component';
import { LoadingService } from 'src/app/services/loading.service';

@Component({
    selector: 'app-datasets',
    templateUrl: './datasets.component.html',
    styleUrls: ['./datasets.component.scss'],
    standalone: false
})

export class DatasetsComponent  implements OnInit {
  editDataset:Dataset;

  @ViewChild("datasetModal", { static: false }) datasetModal: DatasetsModalComponent;
  @Input() width = "";
  @Output() selectedDataset = new EventEmitter<Dataset>();
  dataset: Dataset;

  constructor(public datasetService : DatasetService, public loadingService : LoadingService) {}

  openModal(dataset: Dataset){
    this.editDataset = dataset;    
    this.datasetModal.modal.isOpen = true;
  }

  activeDataset($event: any){
    let dataset_name = document.querySelectorAll('.dataset-name');
    dataset_name.forEach(d_n => {
      d_n.classList.remove('active-dataset')
    });
    $event.target.classList.toggle('active-dataset');    
  }

  selectDataset(dataset: Dataset){
    this.dataset = dataset;
    this.sendDataset(this.dataset);    
  }

  sendDataset(dataset: Dataset){
    this.selectedDataset.emit(dataset);    
  }

  ngOnInit() {}
}