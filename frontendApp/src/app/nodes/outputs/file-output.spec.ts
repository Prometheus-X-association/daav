import { FileOutput } from './file-output';
import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { WorkflowNodeEditor } from 'src/app/core/workflow-node-editor';
import { Injector, inject } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { DatasetFile } from 'src/app/models/dataset-file';
import { DatasetType } from 'src/app/enums/dataset-type';

describe('FileOutput', () => {
  let area: AreaPlugin<any, any>;
  let injector: Injector;
  let mockWorkflowEditor: Partial<WorkflowNodeEditor<Schemes>>;
  let mockDatasetService: any;
  let mockHttp: any;

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
      getDatasets: jasmine.createSpy('getDatasets'),
      urlBack: 'https://api',
      addDatasetToList: jasmine.createSpy('addDatasetToList')
    };
    mockHttp = jasmine.createSpyObj('HttpClient', ['get', 'post', 'put']);

    TestBed.configureTestingModule({
      imports: [],
      providers: [
        { provide: DatasetService, useValue: mockDatasetService },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
      ]
    });

    injector = TestBed.inject(Injector);

    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
    area.update = jasmine.createSpy('update');

    mockWorkflowEditor = { injector };
    Object.defineProperty(area, 'parent', {
      value: mockWorkflowEditor,
      writable: true,
      configurable: true
    });
  });

  it('should create an instance', () => {
    const block = new FileOutput('label', area);
    expect(block).toBeTruthy();
    expect(block.selectControl).toBeDefined();
  });

  it('should add delimiter control when file type is csv', () => {
    const block = new FileOutput('label', area, { data: {} } as any);

    block['addFileTypeControl']('csv');
    expect(block['delimiterControl']).toBeDefined();
    expect(area.update).toHaveBeenCalled();
  });

  it('should remove delimiter control when switching to json', () => {
    const block = new FileOutput('label', area, { data: {} } as any);
    block['addFileTypeControl']('csv');
    block['fileTypeControl'].value = 'json';
    block.fileControlChange({ value: 'json' } as any);
    expect(block['delimiterControl']).toBeNull();
  });

  it('should validate file extensions and detect type from path', () => {
    const block = new FileOutput('label', area);
    expect(block['hasValidFileExtension']('test.csv')).toBeTrue();
    expect(block['getFileTypeFromPath']('test.json')).toBe('json');
    expect(block['getFileTypeFromPath']('unknown.ext')).toBe('csv');
  });

  it('should filter DatasetFile instances with valid paths', () => {
    const block = new FileOutput('label', area);
    const dataset = new DatasetFile({ id: '1', name: 'file', filePath: 'test.csv', folder: '', description: '', type: DatasetType.FilePath } as any);
    expect(block['datasetFilter'](dataset as any)).toBeTrue();
  });
});
