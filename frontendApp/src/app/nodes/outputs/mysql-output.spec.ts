import { AreaPlugin } from 'rete-area-plugin';
import { MysqlOutput } from './mysql-output';
import { Schemes } from 'src/app/core/workflow-editor';
import { WorkflowNodeEditor } from 'src/app/core/workflow-node-editor';
import { Injector } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';

describe('MysqlOutput', () => {
  let area: AreaPlugin<any, any>;
  let injector: Injector;
  let mockWorkflowEditor: Partial<WorkflowNodeEditor<Schemes>>;
  let mockDatasetService: any;

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
      getDatasets: jasmine.createSpy('getDatasets'),
      getContentDataset: jasmine.createSpy('getContentDataset'),
      urlBack: 'https://api'
    };

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
    const block = new MysqlOutput('label', area);
    expect(block).toBeTruthy();
  });

  it('should add and remove table controls', () => {
    const block = new MysqlOutput('label', area);
    block['addInputTable']({ tables: ['one', 'two'] } as any, {} as any);

    expect(block['tableAutoCompleteControl']).toBeDefined();
    block.removeInputTable();
    expect(block['tableAutoCompleteControl']).toBeNull();
  });

  it('should add and remove select exist control', () => {
    const block = new MysqlOutput('label', area);
    block['addSelectExist']({ data: {} } as any);

    expect(block['selectExistControl']).toBeDefined();
    block.removeSelectExist();
    expect(block['selectExistControl']).toBeNull();
  });
});
