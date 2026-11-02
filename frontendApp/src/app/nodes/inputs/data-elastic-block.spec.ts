import { AreaPlugin } from 'rete-area-plugin';
import { Injector, signal } from '@angular/core';
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { DataElasticBlock } from './data-elastic-block';
import { Schemes } from 'src/app/core/workflow-editor';
import { WorkflowNodeEditor } from 'src/app/core/workflow-node-editor';
import { DatasetService } from 'src/app/services/dataset.service';
import { ElasticService } from 'src/app/services/elastic.service';
import { DatasetElasticSearch } from 'src/app/models/dataset-elastic-search';
import { StatusNode } from 'src/app/enums/status-node';

describe('DataElasticBlock', () => {
  let area: AreaPlugin<any, any>;
  let mockDatasetService: any;
  let mockElasticService: jasmine.SpyObj<ElasticService>;
  const sample = { nodeSchema: [], name: 'products', dataExample: {} } as any;

  function dataset(index?: string): DatasetElasticSearch {
    return new DatasetElasticSearch({ id: 'ds1', name: 'es', type: 'elastic', index } as any);
  }

  function block(ds = dataset()): DataElasticBlock {
    mockDatasetService.datasets.set([ds]);
    const b = new DataElasticBlock('label', area);
    b.selectControl.value = ds.id;
    return b;
  }

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
      getContentDataset: jasmine.createSpy('getContentDataset').and.returnValue(of({ indices: ['customers', 'products'] })),
      urlBack: 'https://api',
    };
    mockElasticService = jasmine.createSpyObj('ElasticService', ['sample']);
    mockElasticService.sample.and.returnValue(of(sample));

    TestBed.configureTestingModule({
      providers: [
        { provide: DatasetService, useValue: mockDatasetService },
        { provide: ElasticService, useValue: mockElasticService },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting(),
      ],
    });
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
    area.update = jasmine.createSpy('update');
    const mockWorkflowEditor: Partial<WorkflowNodeEditor<Schemes>> = {
      injector: TestBed.inject(Injector),
      getConnections: () => [],
    } as any;
    Object.defineProperty(area, 'parent', { value: mockWorkflowEditor, writable: true, configurable: true });
  });

  it('should list the indices when the dataset has no index', async () => {
    const b = block();
    await b.dataSourceChange({ value: 'ds1' } as any);
    expect(mockDatasetService.getContentDataset).toHaveBeenCalled();
    expect(b.selectControlIndex.list.map((i) => i.value)).toEqual(['customers', 'products']);
    expect(b.outputs['out']).toBeUndefined();
  });

  it('should preview directly when the dataset fixes the index', async () => {
    const b = block(dataset('products'));
    await b.dataSourceChange({ value: 'ds1' } as any);
    expect(mockDatasetService.getContentDataset).not.toHaveBeenCalled();
    expect(mockElasticService.sample).toHaveBeenCalledWith('ds1', jasmine.objectContaining({ index: 'products' }));
    expect(b.outputs['out']).toBeDefined();
    expect(b.status).toBe(StatusNode.Complete);
  });

  it('should send the query options with the preview', async () => {
    const b = block();
    await b.dataSourceChange({ value: 'ds1' } as any);
    // the select widget updates its value before calling back
    b.selectControlIndex.value = 'products';
    b.indexChange({ value: 'products' } as any);
    b.queryControl.value = 'category:books';
    b.fieldsControl.value = ' name, price ,';
    b.includeIdControl.value = false;
    b.refreshPreview();
    expect(mockElasticService.sample).toHaveBeenCalledWith('ds1', {
      index: 'products',
      query: 'category:books',
      fields: ['name', 'price'],
      size: 5,
      includeId: false,
    });
  });

  it('should debounce the preview while typing', fakeAsync(() => {
    const b = block(dataset('products'));
    b.addOptionControls(null);
    b.schedulePreview();
    b.schedulePreview();
    tick(500);
    expect(mockElasticService.sample).not.toHaveBeenCalled();
    tick(800);
    expect(mockElasticService.sample).toHaveBeenCalledTimes(1);
  }));

  it('should show the backend error', async () => {
    mockElasticService.sample.and.returnValue(throwError(() => ({ error: { detail: 'Invalid JSON query' } })));
    const b = block(dataset('products'));
    await b.dataSourceChange({ value: 'ds1' } as any);
    expect(b.status).toBe(StatusNode.Error);
    expect(b.statusMessage).toBe('Invalid JSON query');
  });

  it('should restore its controls from a saved node', () => {
    mockDatasetService.datasets.set([dataset()]);
    const b = new DataElasticBlock('label', area, {
      data: {
        selectIndexDataSource: { value: 'products', list: [{ label: 'products', value: 'products' }], label: 'Index' },
        query: { value: 'a:1', list: [], type: 'text' },
        fields: { value: '', list: [], type: 'text' },
        maxDocs: { value: '10', list: [], type: 'number' },
        includeId: { value: false },
      },
    } as any);
    const data = b.data() as any;
    expect(data.selectIndexDataSource.value).toBe('products');
    expect(data.query.value).toBe('a:1');
    expect(data.maxDocs.value).toBe('10');
    expect(data.includeId.value).toBeFalse();
  });
});
