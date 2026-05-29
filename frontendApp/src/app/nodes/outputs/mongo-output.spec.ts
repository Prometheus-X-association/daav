import { AreaPlugin } from 'rete-area-plugin';
import { MongoOutput } from './mongo-output';
import { Schemes } from 'src/app/core/workflow-editor';
import { WorkflowNodeEditor } from 'src/app/core/workflow-node-editor';
import { Injector } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';

describe('MongoOutput', () => {
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
    const block = new MongoOutput('label', area);
    expect(block).toBeTruthy();
  });

  it('should add and remove collection controls', () => {
    const block = new MongoOutput('label', area);
    block['addInputCollection']({ collections: ['one', 'two'] } as any, {} as any);

    expect(block['collectionAutoCompleteControl']).toBeDefined();
    block.removeInputCollection();
    expect(block['collectionAutoCompleteControl']).toBeNull();
  });

  it('should add and remove select exist control', () => {
    const block = new MongoOutput('label', area);
    block['addSelectExist']({ data: {} } as any);

    expect(block['selectExistControl']).toBeDefined();
    block.removeSelectExist();
    expect(block['selectExistControl']).toBeNull();
  });
});

