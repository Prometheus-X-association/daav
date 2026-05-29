import '@angular/localize/init';
import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule, IonModal } from '@ionic/angular';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { HttpEventType } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { DatasetsModalComponent } from './datasets-modal.component';
import { DatasetService } from 'src/app/services/dataset.service';

describe('DatasetsModalComponent', () => {
  let component: DatasetsModalComponent;
  let fixture: ComponentFixture<DatasetsModalComponent>;
  let datasetServiceSpy: jasmine.SpyObj<DatasetService>;

  beforeEach(waitForAsync(() => {
    datasetServiceSpy = jasmine.createSpyObj('DatasetService', ['addDataset', 'get', 'edit', 'uploadFile']);
    datasetServiceSpy.addDataset.and.returnValue(of({}));
    datasetServiceSpy.get.and.returnValue(undefined as any);
    datasetServiceSpy.edit.and.returnValue(undefined as any);
    datasetServiceSpy.uploadFile.and.returnValue(of());

    TestBed.configureTestingModule({
      declarations: [DatasetsModalComponent],
      imports: [IonicModule.forRoot(), HttpClientTestingModule],
      providers: [{ provide: DatasetService, useValue: datasetServiceSpy }]
    }).compileComponents();

    fixture = TestBed.createComponent(DatasetsModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    component.modal = { isOpen: true, dismiss: jasmine.createSpy('dismiss') } as any;
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should populate form values on dataset change', () => {
    const dataset = {
      name: 'myDataset',
      type: 'file',
      folder: 'folder',
      filePath: 'path',
      inputType: 'file',
      csvHeader: 'header',
      csvDelimiter: ';',
      uri: 'uri',
      database: 'db',
      collection: 'collection',
      host: 'host',
      user: 'user',
      password: 'pass',
      table: 'table',
      url: 'url',
      index: 'index',
      key: 'key',
      bearerToken: 'token',
      apiAuth: 'auth',
      clientId: 'clientId',
      clientSecret: 'clientSecret',
      authUrl: 'authUrl',
      basicToken: 'basicToken',
      service_key: 'serviceKey',
      secret_key: 'secretKey'
    } as any;

    component.dataset = dataset;
    component.ngOnChanges({
      dataset: {
        currentValue: dataset,
        previousValue: null,
        firstChange: true,
        isFirstChange: () => true
      } as any
    });

    expect(component.formDatabase.get('name')?.value).toBe('myDataset');
    expect(component.formDatabase.get('type')?.value).toBe('file');
  });

  it('should add a dataset and close the modal when no dataset is provided', () => {
    component.dataset = undefined;

    component.addConnection({});

    expect(datasetServiceSpy.addDataset).toHaveBeenCalled();
    expect(component.modal.isOpen).toBeFalse();
    expect((component.modal as any).dismiss).toHaveBeenCalled();
  });

  it('should edit an existing dataset and close the modal', () => {
    component.dataset = { id: '123', name: 'existing dataset' } as any;

    component.addConnection({});

    expect(datasetServiceSpy.edit).toHaveBeenCalledWith(component.dataset);
    expect(component.modal.isOpen).toBeFalse();
    expect((component.modal as any).dismiss).toHaveBeenCalled();
  });

  it('should not call uploadFile for unsupported formats', () => {
    const file = new File(['content'], 'test.exe', { type: 'application/octet-stream' });

    component.uploadFile({ target: { type: 'file', files: [file] } } as any);

    expect(component.isCsvFile).toBeFalse();
    expect(datasetServiceSpy.uploadFile).not.toHaveBeenCalled();
  });

  it('should upload CSV files and update form values on response', async () => {
    const file = new File(['a,b'], 'test.csv', { type: 'text/csv' });
    datasetServiceSpy.uploadFile.and.returnValue(
      of(
        { type: HttpEventType.UploadProgress, loaded: 50, total: 100 } as any,
        { type: HttpEventType.Response, body: [{ filepath: 'file-path' }] } as any
      )
    );

    component.uploadFile({ target: { type: 'file', files: [file] } } as any);

    expect(component.isCsvFile).toBeTrue();
    expect(component.formDatabase.get('filePath')?.value).toBe('file-path');
    expect(component.formDatabase.get('inputType')?.value).toBe('file');
  });

  it('should set folder path when upload response returns multiple items', async () => {
    const file = new File(['a,b'], 'test.csv', { type: 'text/csv' });
    datasetServiceSpy.uploadFile.and.returnValue(
      of(
        { type: HttpEventType.UploadProgress, loaded: 50, total: 100 } as any,
        { type: HttpEventType.Response, body: [{ folder: 'folder-path', filepath: 'file-path' }, { folder: 'folder-path-2' }] } as any
      )
    );

    component.uploadFile({ target: { type: 'file', files: [file] } } as any);

    expect(component.formDatabase.get('folder')?.value).toBe('folder-path');
    expect(component.formDatabase.get('filePath')?.value).toBe('folder-path');
    expect(component.formDatabase.get('inputType')?.value).toBe('folder');
  });

  it('should reset upload progress on upload error', () => {
    const file = new File(['a,b'], 'test.csv', { type: 'text/csv' });
    datasetServiceSpy.uploadFile.and.returnValue(throwError(() => new Error('upload failed')));

    component.uploadProgress = 50;
    component.uploadFile({ target: { type: 'file', files: [file] } } as any);

    expect(component.uploadProgress).toBeNull();
  });

  it('should toggle selected class on radio elements', () => {
    const first = document.createElement('div');
    const second = document.createElement('div');
    first.classList.add('datatypes-radio', 'selected');
    second.classList.add('datatypes-radio');
    document.body.appendChild(first);
    document.body.appendChild(second);

    component.onSelected({ target: second } as any);

    expect(first.classList.contains('selected')).toBeFalse();
    expect(second.classList.contains('selected')).toBeTrue();

    document.body.removeChild(first);
    document.body.removeChild(second);
  });

  it('should close the modal when closeModalAddConnection is called', () => {
    component.modal = { isOpen: true, dismiss: jasmine.createSpy('dismiss') } as any;
    component.closeModalAddConnection();
    expect(component.modal.isOpen).toBeFalse();
  });
});
