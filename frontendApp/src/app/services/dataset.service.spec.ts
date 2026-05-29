import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { DatasetService } from './dataset.service';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';
import { DatasetType } from '../enums/dataset-type';
import { DatasetFile } from '../models/dataset-file';

describe('DatasetService', () => {
  let service: DatasetService;
  let httpMock: HttpTestingController;
  let matDialog: jasmine.SpyObj<MatDialog>;

  beforeEach(() => {
    matDialog = jasmine.createSpyObj('MatDialog', ['open']);
    matDialog.open.and.returnValue({ afterClosed: () => of(true) } as any);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [{ provide: MatDialog, useValue: matDialog }]
    });
    service = TestBed.inject(DatasetService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should resolve exportDaav on success', async () => {
    const project = { id: 'p1' } as any;
    const promise = service.exportDaav(project);
    const req = httpMock.expectOne(`${service['urlBack']}/exportDaav`);
    expect(req.request.method).toBe('POST');
    req.flush(['ok']);

    await expectAsync(promise).toBeResolvedTo(['ok']);
  });

  it('should reject exportDaav on error', async () => {
    const promise = service.exportDaav({} as any);
    const req = httpMock.expectOne(`${service['urlBack']}/exportDaav`);
    expect(req.request.method).toBe('POST');
    req.flush('error', { status: 500, statusText: 'Server Error' });

    await expectAsync(promise).toBeRejected();
  });

  it('should update files from pathBack and resolve data', async () => {
    const promise = service.pathBack();
    const req = httpMock.expectOne(`${service['urlBack']}/getPaths`);
    expect(req.request.method).toBe('GET');
    req.flush([{ filepath: '/tmp', folder: 'data' }]);

    await expectAsync(promise).toBeResolved();
    expect(service['files']).toEqual([{ filepath: '/tmp', folder: 'data' }]);
  });

  it('should map getDatasets response to DatasetFile instances', () => {
    const response = [{ type: DatasetType.FilePath, filePath: '/tmp/data.csv' }];
    service.getDatasets().subscribe((datasets) => {
      expect(datasets.length).toBe(1);
      expect(datasets[0]).toBeInstanceOf(DatasetFile);
      expect((datasets[0] as DatasetFile).filePath).toBe('/tmp/data.csv');
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/`);
    expect(req.request.method).toBe('GET');
    req.flush(response);
  });

  it('should add a dataset to the list and prevent duplicates', () => {
    const dataset = { id: 'd1' } as any;
    service.addDatasetToList(dataset);
    service.addDatasetToList(dataset);

    expect(service.datasets().length).toBe(1);
    expect(service.datasets()[0].id).toBe('d1');
  });

  it('should call dialog open and delete dataset when confirmed', () => {
    const dataset = { id: 'd1' } as any;
    spyOn(service, 'deleteDataset').and.returnValue(of({}));
    spyOn(service, 'get').and.stub();

    service.delete(dataset);

    expect(matDialog.open).toHaveBeenCalled();
    expect(service.deleteDataset).toHaveBeenCalledWith(dataset);
    expect(service.get).toHaveBeenCalled();
  });

  it('should return PTX data resource url', () => {
    const connectionId = 'conn123';
    let result: any;
    service.getPTXDataresource(connectionId).subscribe((res) => {
      result = res;
    });

    const req = httpMock.expectOne(`${service['urlBack']}/ptx/dataResources/${connectionId}`);
    expect(req.request.method).toBe('GET');
    req.flush({ ok: true });
    expect(result).toEqual({ ok: true });
  });

  it('should use get after editing a dataset', () => {
    const dataset = { id: 'd1' } as any;
    spyOn(service, 'editDataset').and.returnValue(of({}));
    spyOn(service, 'get').and.stub();

    service.edit(dataset);

    expect(service.editDataset).toHaveBeenCalledWith(dataset);
    expect(service.get).toHaveBeenCalled();
  });

  it('should not delete dataset when dialog is closed without confirmation', () => {
    matDialog.open.and.returnValue({ afterClosed: () => of(false) } as any);
    const dataset = { id: 'd1' } as any;
    spyOn(service, 'deleteDataset').and.returnValue(of({}));
    spyOn(service, 'get').and.stub();

    service.delete(dataset);

    expect(service.deleteDataset).not.toHaveBeenCalled();
    expect(service.get).not.toHaveBeenCalled();
  });

  it('should fetch datasets into the signal when get() is called', () => {
    const response = [{ type: DatasetType.FilePath, filePath: '/tmp/data.csv' }];
    spyOn(service, 'datasets').and.callThrough();

    service.get();

    const req = httpMock.expectOne(`${service['apiUrl']}/`);
    req.flush(response);

    expect(service.datasets().length).toBe(1);
    expect(service.datasets()[0]).toEqual(jasmine.any(DatasetFile));
  });

  it('should call collectionBack and update files', async () => {
    const promise = service.collectionBack();
    const req = httpMock.expectOne(`${service['urlBack']}/getCollections`);
    expect(req.request.method).toBe('GET');
    req.flush([{ folder: 'col1' }]);

    await expectAsync(promise).toBeResolved();
    expect(service['files']).toEqual([{ folder: 'col1' }]);
  });

  it('should call tableBack and update files', async () => {
    const promise = service.tableBack();
    const req = httpMock.expectOne(`${service['urlBack']}/getTables`);
    expect(req.request.method).toBe('GET');
    req.flush([{ folder: 'table1' }]);

    await expectAsync(promise).toBeResolved();
    expect(service['files']).toEqual([{ folder: 'table1' }]);
  });

  it('should post getContentDataset correctly', () => {
    service.getContentDataset({} as any, { perPage: 1, page: 1 }, { database: '', table: '' }).subscribe();
    const req = httpMock.expectOne(`${service['apiUrl']}/getContentDataset`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.pagination.perPage).toBe(1);
    req.flush({});
  });

  it('should post getDfContentDataset correctly', () => {
    service.getDfContentDataset({} as any, { perPage: 1, page: 1 }, { database: '', table: '' }).subscribe();
    const req = httpMock.expectOne(`${service['apiUrl']}/getDfContentDataset`);
    expect(req.request.method).toBe('POST');
    req.flush({});
  });

  it('should post getDfFromJson correctly', () => {
    service.getDfFromJson('json string').subscribe();
    const req = httpMock.expectOne(`${service['apiUrl']}/getDfFromJson`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.data).toBe('json string');
    req.flush({});
  });

  it('should put editDataset correctly', () => {
    service.editDataset({ id: 'd1' } as any).subscribe();
    const req = httpMock.expectOne(`${service['apiUrl']}/`);
    expect(req.request.method).toBe('PUT');
    req.flush({});
  });

  it('should delete dataset correctly', () => {
    service.deleteDataset({ id: 'd1' } as any).subscribe();
    const req = httpMock.expectOne(`${service['apiUrl']}/d1`);
    expect(req.request.method).toBe('DELETE');
    req.flush({});
  });
});
