import { Component, Input, Output, EventEmitter, ViewChild, inject } from '@angular/core';
// import { Observable } from 'rxjs';
import { Dataset } from 'src/app/models/dataset';
import { DatasetService } from 'src/app/services/dataset.service';
import { DatasetsModalComponent } from '../../datasets-modal/datasets-modal.component';
import { LoadingService } from 'src/app/services/loading.service';
import { IonButton, IonIcon, IonItem, IonList } from '@ionic/angular/standalone';
import { addIcons } from 'ionicons';
import { createOutline, trashOutline } from 'ionicons/icons';
import { NgClass } from '@angular/common';

@Component({
    selector: 'app-datasets',
    templateUrl: './datasets.component.html',
    styleUrls: ['./datasets.component.scss'],
    imports: [IonButton, IonIcon, IonItem, IonList, NgClass, DatasetsModalComponent]
})

export class DatasetsComponent {
  datasetService = inject(DatasetService);
  loadingService = inject(LoadingService);

  editDataset:Dataset;

  @ViewChild("datasetModal", { static: false }) datasetModal: DatasetsModalComponent;
  @Input() width = "";
  @Output() selectedDataset = new EventEmitter<Dataset>();
  dataset: Dataset;

  constructor() {
    addIcons({ createOutline, trashOutline });
  }

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

}
