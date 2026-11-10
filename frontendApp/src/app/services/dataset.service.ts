import { DatasetFile } from '../models/dataset-file';
import { DatasetApi } from '../models/dataset-api';
import { DatasetMongo } from './../models/dataset-mongo';
import { DatasetMySQL } from './../models/dataset-my-sql';
import { DatasetElasticSearch } from '../models/dataset-elastic-search';
import { Injectable, inject, signal } from '@angular/core';
import { Dataset } from '../models/dataset';
import { Observable, map, firstValueFrom } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { DatasetType } from '../enums/dataset-type';
import { DatasetsI } from '../models/datasets-i';
import { Project } from '../models/interfaces/project';
import { BaseService } from './base.service.service';
import {
  Pagination,
  DatasetContentParams,
  DatasetResponseMap,
} from '../models/dataset-content-response';
import { DatasetPTX } from '../models/dataset-ptx';
import { MatDialog } from '@angular/material/dialog';
import { NodeDataPandasDf } from '../models/node-data';
import { ConfirmDeletionModalComponent } from '../components/confirm-deletion-modal/confirm-deletion-modal.component';

@Injectable({
  providedIn: 'root',
})
export class DatasetService extends BaseService {
  private readonly apiUrl = this.urlBack + '/datasets';

  readonly dialog = inject(MatDialog);

  private readonly datasetsSignal = signal<Dataset[]>([]);
  datasets = this.datasetsSignal.asReadonly();

  pagination: { perPage: number; page: number } = {
    perPage: 100,
    page: 1,
  };
  datasetParams: { database: string; table: string } = {
    database: '',
    table: '',
  };

  fiches: Array<any> = [];
  files: Array<any> = [];

  constructor(private readonly http: HttpClient) {
    super();
  }
  exportDaav(projectDaav: Project) {
    return new Promise<Array<string>>((resolve, reject) => {
      this.http.post(this.urlBack + '/exportDaav', projectDaav).subscribe({
        next: (data: any) => {
          console.log('response', data);
          resolve(data);
        },
        error: (err: any) => {
          console.log('errrr', err);
          console.error(err);
          reject();
        },
      });
    });
  }

  pathBack() {
    return new Promise<Array<string>>((resolve, reject) => {
      this.http.get(this.urlBack + '/getPaths').subscribe({
        next: (data: any) => {
          console.log(data);
          this.files = data;
          console.log(Object.keys(this.files[0]));
          resolve(data);
        },
        error: (err: any) => {
          console.error(err);
          reject();
        },
      });
    });
  }

  collectionBack() {
    return new Promise<Array<string>>((resolve, reject) => {
      this.http.get(this.urlBack + '/getCollections').subscribe({
        next: (data: any) => {
          console.log(data);
          this.files = data;
          console.log(Object.keys(this.files[0]));
          resolve(data);
        },
        error: (err: any) => {
          console.error(err);
          reject();
        },
      });
    });
  }

  tableBack() {
    return new Promise<Array<string>>((resolve, reject) => {
      this.http.get(this.urlBack + '/getTables').subscribe({
        next: (data: any) => {
          console.log(data);
          this.files = data;
          console.log(Object.keys(this.files[0]));
          resolve(data);
        },
        error: (err: any) => {
          console.error(err);
          reject();
        },
      });
    });
  }

  addDataset(data: any) {
    return this.http.post(this.apiUrl + '/', data);
  }

  uploadFile(data: FormData) {
    return this.http.post<[{ filepath: string; folder: string }]>(
      this.apiUrl + '/uploadFile',
      data,
      {
        reportProgress: true,
        observe: 'events',
      }
    );
  }

  getDatasets(): Observable<Dataset[]> {
    return this.http.get<DatasetsI[]>(this.apiUrl + '/').pipe(
      map((val: DatasetsI[]) => {
        const datasets: Dataset[] = [];
        val.forEach((element) => {
          switch (element.type) {
            case DatasetType.FilePath:
              datasets.push(new DatasetFile(element));
              break;
            case DatasetType.Mongo:
              datasets.push(new DatasetMongo(element));
              break;
            case DatasetType.MySQL:
              datasets.push(new DatasetMySQL(element));
              break;
            case DatasetType.API:
              datasets.push(new DatasetApi(element));
              break;
            case DatasetType.ElasticSearch:
              datasets.push(new DatasetElasticSearch(element));
              break;
            case DatasetType.PTX:
              datasets.push(new DatasetPTX(element));
              break;
            default:
              break;
          }
        });
        return datasets;
      })
    );
  }

  getContentDataset<T extends Dataset>(
    dataset: T,
    paginationParams?: Pagination,
    datasetParams?: DatasetContentParams
  ) {
    const data = {
      dataset,
      pagination: paginationParams ? paginationParams : this.pagination,
      datasetParams: datasetParams ? datasetParams : this.datasetParams,
    };
    return this.http.post<DatasetResponseMap<T>>(
      this.apiUrl + '/getContentDataset',
      data
    );
  }

  getDfContentDataset<T extends Dataset>(
    dataset: T,
    paginationParams?: Pagination,
    datasetParams?: DatasetContentParams
  ) {
    const data = {
      dataset,
      pagination: paginationParams ? paginationParams : this.pagination,
      datasetParams: datasetParams ? datasetParams : this.datasetParams,
    };
    return this.http.post<NodeDataPandasDf>(
      this.apiUrl + '/getDfContentDataset',
      data
    );
  }

  getDfFromJson(jsonData: string) {
    const data = {
      data: jsonData,
    };
    return this.http.post<NodeDataPandasDf>(
      this.apiUrl + '/getDfFromJson',
      data
    );
  }

  editDataset(dataset: Dataset) {
    return this.http.put(this.apiUrl + '/', dataset);
  }

  deleteDataset(dataset: Dataset) {
    return this.http.delete(this.apiUrl + '/' + dataset.id + '');
  }

  get() {
    this.getDatasets().subscribe((datasets) => {
      this.datasetsSignal.set(datasets);
    });
  }

  edit(dataset: Dataset) {
    this.editDataset(dataset).subscribe((res) => {
      this.get();
    });
  }

  delete(dataset: Dataset) {
    const dialogRef = this.dialog.open(ConfirmDeletionModalComponent, {
      data: { message: 'Do you really want to delete this dataset ?' }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.deleteDataset(dataset).subscribe((res) => {
          this.get();
          console.log(res);
        });
      }
    })
  }

  getPTXDataresource(connectionId: string) {
    return this.http.get(this.urlBack + '/ptx/dataResources/' + connectionId);
  }

  /**
   * Add a new dataset to the list and update the signal
   * @param dataset The new dataset to add
   */
  addDatasetToList(dataset: Dataset) {
    this.datasetsSignal.update(datasets => {
      // Check if dataset already exists
      const exists = datasets.some(d => d.id === dataset.id);
      if (!exists) {
        return [...datasets, dataset];
      }
      return datasets;
    });
  }

  /**
   * Create and add a new dataset, then update the list
   * @param data The dataset data to create
   */
  async createAndAddDataset(data: any) {
    try {
      const response = await firstValueFrom(this.addDataset(data));
      if (response) {
        // Refresh the entire dataset list
        this.get();
        return response;
      }
    } catch (error) {
      console.error('Error creating dataset:', error);
      throw error;
    }
    return null; // Ensure all code paths return a value
  }

  /**
   * Clear all datasets from cache (called on logout)
   */
  clearDatasets(): void {
    this.datasetsSignal.set([]);
  }
}
