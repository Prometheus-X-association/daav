import { HttpEventType } from '@angular/common/http';
import {
  Component,
  Input,
  OnChanges,
  OnInit,
  SimpleChanges,
  ViewChild,
  ViewChildren,
} from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { IonModal, IonRadio } from '@ionic/angular';
import { Dataset } from 'src/app/models/dataset';
import { DatasetService } from 'src/app/services/dataset.service';

@Component({
    selector: 'app-datasets-modal',
    templateUrl: './datasets-modal.component.html',
    styleUrls: ['./datasets-modal.component.scss'],
    standalone: false
})
export class DatasetsModalComponent implements OnChanges {
  @ViewChild('modal') modal: IonModal;

  @Input() dataset: Dataset;

  public datasetTypes = [
    { dataName: 'MySQL', dataType: 'mysql', logo: 'logo-ionic' },
    { dataName: 'MongoDB', dataType: 'mongo', logo: 'logo-ionic' },
    { dataName: 'Elastic search', dataType: 'elastic', logo: 'logo-ionic' },
    { dataName: 'File', dataType: 'file', logo: 'logo-ionic' },
    { dataName: 'API', dataType: 'api', logo: 'logo-ionic' },
    { dataName: 'PTX', dataType: 'ptx', logo: 'logo-ionic' },
  ];

  public uploadProgress: number | null = null;

  apiAuth: string = '';

  public acceptedFormats: string[] = [
    '.csv',
    '.json',
    '.parquet',
    '.xlsx',
    '.xls',
    '.tsv',
    '.avro',
    '.feather',
    '.orc',
    '.txt',
    '.yml',
    '.yaml',
    '.xml',
    '.log',
    '.md',
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.bmp',
    '.tiff',
    '.webp',
    '.svg',
    '.mp3',
    '.wav',
    '.flac',
    '.aac',
    '.ogg',
    '.m4a',
    '.wma',
    '.mp4',
    '.avi',
    '.mkv',
    '.mov',
    '.wmv',
    '.flv',
    '.webm',
    '.m4v',
  ];

  formDatabase: FormGroup<{
    name: FormControl<string | null>;
    type: FormControl<string | null>;
    folder: FormControl<string | null>;
    filePath: FormControl<string | null>;
    file: FormControl<File | null>;
    inputType: FormControl<string | null>;
    csvHeader: FormControl<string | null>;
    csvDelimiter: FormControl<string | null>;
    uri: FormControl<string | null>;
    database: FormControl<string | null>;
    collection: FormControl<string | null>;
    host: FormControl<string | null>;
    user: FormControl<string | null>;
    password: FormControl<string | null>;
    table: FormControl<string | null>;
    url: FormControl<string | null>;
    index: FormControl<string | null>;
    key: FormControl<string | null>;
    bearerToken: FormControl<string | null>;
    apiAuth: FormControl<string | null>;
    clientId: FormControl<string | null>;
    clientSecret: FormControl<string | null>;
    authUrl: FormControl<string | null>;
    basicToken: FormControl<string | null>;
    service_key: FormControl<string | null>;
    secret_key: FormControl<string | null>;
  }>;

  public isCsvFile: boolean = false;

  constructor(public datasetService: DatasetService) {
    this.formDatabase = new FormGroup({
      name: new FormControl<string | null>('', Validators.required),
      type: new FormControl<string | null>('', Validators.required),
      folder: new FormControl<string | null>('', Validators.required),
      filePath: new FormControl<string | null>('', Validators.required),
      file: new FormControl<File | null>(null, Validators.required),
      inputType: new FormControl<string | null>('', Validators.required),
      csvHeader: new FormControl<string | null>('', Validators.required),
      csvDelimiter: new FormControl<string | null>('', Validators.required),
      uri: new FormControl<string | null>('', Validators.required),
      database: new FormControl<string | null>('', Validators.required),
      collection: new FormControl<string | null>('', Validators.required),
      host: new FormControl<string | null>('', Validators.required),
      user: new FormControl<string | null>('', Validators.required),
      password: new FormControl<string | null>('', Validators.required),
      table: new FormControl<string | null>('', Validators.required),
      url: new FormControl<string | null>('', Validators.required),
      index: new FormControl<string | null>('', Validators.required),
      key: new FormControl<string | null>('', Validators.required),
      bearerToken: new FormControl<string | null>('', Validators.required),
      apiAuth: new FormControl<string | null>('', Validators.required),
      clientId: new FormControl<string | null>('', Validators.required),
      clientSecret: new FormControl<string | null>('', Validators.required),
      authUrl: new FormControl<string | null>('', Validators.required),
      basicToken: new FormControl<string | null>('', Validators.required),
      service_key: new FormControl<string | null>('', Validators.required),
      secret_key: new FormControl<string | null>('', Validators.required),
    });
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.dataset) {
      Object.keys(this.dataset).forEach((key) => {
        const control = this.formDatabase.get(key);
        if (control) {
          control.setValue(this.dataset[key]);
        }
      });
    }
  }

  editDataset(dataset: Dataset) {
    this.datasetService.edit(dataset);
  }

  addConnection($event: any) {
    // send to FastAPI
    if (!this.dataset) {
      // Clean form data: exclude 'file' field (File object with fakepath)
      // Only send 'filePath' which contains the URN from uploadFile()
      const formData = { ...this.formDatabase.value };
      delete formData.file; // Remove File object to avoid sending fakepath

      this.datasetService.addDataset(formData).subscribe(() => {
        this.datasetService.get();
      });
    } else {
      let formKeys = Object.entries(this.formDatabase.value);
      formKeys.forEach((fK) => {
        let key = fK[0];
        let value = fK[1];
        // Skip 'file' field when editing
        if (key !== 'file' && key in this.dataset) {
          this.dataset[key] = value;
        }
      });
      this.editDataset(this.dataset);
    }

    // close modal
    this.modal.isOpen = false;
    this.modal.dismiss();
  }

  uploadFile(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input) return;

    // Reset CSV flag
    this.isCsvFile = false;
    if (input.type === 'file' && input.files) {
      const formData = new FormData();
      Array.from(input.files).forEach((file: File, index: number) => {
        const ext = '.' + input.files[0].name.split('.').pop()?.toLowerCase();
        if (!this.acceptedFormats.includes(ext)) {
          console.error('Format not supported:', ext);
          return;
        }
        if (input.files.length === 1 && (ext === '.csv' || ext === '.tsv')) {
          this.isCsvFile = true;
        }
        formData.append('file', file);
      });
      this.uploadProgress = 0;
      this.datasetService.uploadFile(formData).subscribe({
        next: (event) => {
          if (event.type === HttpEventType.UploadProgress && event.total) {
            this.uploadProgress = Math.round(
              (100 * event.loaded) / event.total
            );
          } else if (event.type === HttpEventType.Response) {
            this.uploadProgress = null;
            event.body;
            if (event.body && event.body.length > 1) {
              this.formDatabase
                .get('folder')
                ?.setValue(event.body[0].folder);
                this.formDatabase
                .get('filePath')
                ?.setValue(event.body[0].folder);
                this.formDatabase
                .get('inputType')?.setValue('folder');
            } else {
              this.formDatabase
                .get('filePath')
                ?.setValue(event.body[0].filepath);
                this.formDatabase
                .get('inputType')?.setValue('file');
            }
          }
        },
        error: () => {
          this.uploadProgress = null; // reset on error
        },
      });
    }
  }

  onSelectionChange() {}

  onSelected($event) {
    let radios = document.querySelectorAll('.datatypes-radio');
    radios.forEach((r) => {
      if (r.classList.contains('selected') && r !== $event.target) {
        r.classList.remove('selected');
      }
    });
    $event.target.classList.toggle('selected');
  }

  closeModalAddConnection() {
    this.modal.isOpen = false;
  }
}
