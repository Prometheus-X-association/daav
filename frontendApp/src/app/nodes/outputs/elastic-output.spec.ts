import { AreaPlugin } from 'rete-area-plugin';
import { Injector, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { ElasticOutput } from './elastic-output';
import { Schemes } from 'src/app/core/workflow-editor';
import { WorkflowNodeEditor } from 'src/app/core/workflow-node-editor';
import { DatasetService } from 'src/app/services/dataset.service';
import { DatasetElasticSearch } from 'src/app/models/dataset-elastic-search';
import { StatusNode } from 'src/app/enums/status-node';
import { AllSocket, DeepObjectSocket, FlatObjectSocket } from 'src/app/core/sockets/sockets';

describe('ElasticOutput', () => {
  let area: AreaPlugin<any, any>;
  let mockDatasetService: any;

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
      getContentDataset: jasmine.createSpy('getContentDataset').and.returnValue(of({ indices: ['products'] })),
      urlBack: 'https://api',
    };
    TestBed.configureTestingModule({
      providers: [
        { provide: DatasetService, useValue: mockDatasetService },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting(),
      ],
    });
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
    area.update = jasmine.createSpy('update');
    const mockWorkflowEditor: Partial<WorkflowNodeEditor<Schemes>> = { injector: TestBed.inject(Injector) };
    Object.defineProperty(area, 'parent', { value: mockWorkflowEditor, writable: true, configurable: true });
  });

  function datasetWithIndex(index?: string) {
    const ds = new DatasetElasticSearch({ id: 'ds1', name: 'es', type: 'elastic', index } as any);
    mockDatasetService.datasets.set([ds]);
    return ds;
  }

  it('should create an incomplete node with an input', () => {
    const block = new ElasticOutput('label', area);
    expect(block.inputs['export']).toBeDefined();
    expect(block.status).toBe(StatusNode.Incomplete);
  });

  it('should accept flat data (Flatten output) as well as nested data', () => {
    const block = new ElasticOutput('label', area);
    const input = block.inputs['export'].socket;
    expect(input).toBeInstanceOf(AllSocket);
    // compatibility is checked by the source socket (the Sockets type does not list AllSocket)
    expect(new FlatObjectSocket().isCompatibleWith(input as never)).toBeTrue();
    expect(new DeepObjectSocket().isCompatibleWith(input as never)).toBeTrue();
  });

  it('should suggest existing indices and default to the dataset index', () => {
    datasetWithIndex('products');
    const block = new ElasticOutput('label', area);
    block.dataSourceChange({ value: 'ds1' } as any);
    expect(block.indexAutoCompleteControl.list).toEqual(['products']);
    expect(block.indexAutoCompleteControl.value).toBe('products');
    expect(block.selectExistControl.value).toBe('fail');
    expect(block.status).toBe(StatusNode.Complete);
  });

  it('should stay usable when indices cannot be listed', () => {
    datasetWithIndex();
    mockDatasetService.getContentDataset.and.returnValue(throwError(() => ({ status: 502 })));
    const block = new ElasticOutput('label', area);
    block.dataSourceChange({ value: 'ds1' } as any);
    expect(block.indexAutoCompleteControl).toBeDefined();
    expect(block.status).toBe(StatusNode.Incomplete);
  });

  it('should remove its controls when the data source changes', () => {
    datasetWithIndex('products');
    const block = new ElasticOutput('label', area);
    block.dataSourceChange({ value: 'ds1' } as any);
    block.dataSourceChange({ value: null } as any);
    expect(block.indexAutoCompleteControl).toBeNull();
    expect(block.selectExistControl).toBeNull();
    expect(block.idFieldControl).toBeNull();
  });

  it('should export its options', () => {
    datasetWithIndex('products');
    const block = new ElasticOutput('label', area);
    block.dataSourceChange({ value: 'ds1' } as any);
    block.idFieldControl.value = 'sku';
    const data = block.data() as any;
    expect(data.indexAutoComplete.value).toBe('products');
    expect(data.selectExist.value).toBe('fail');
    expect(data.idField.value).toBe('sku');
  });
});
