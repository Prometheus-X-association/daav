import { AreaPlugin } from 'rete-area-plugin';
import { ClassicPreset } from 'rete';
import { DataMongoBlock } from './data-mongo-block';
import { Schemes } from 'src/app/core/workflow-editor';
import { Injector } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { MatSelectChange } from '@angular/material/select';
import { DeepObjectSocket } from 'src/app/core/sockets/sockets';
import { Node } from 'src/app/models/interfaces/node';

describe('DataMongoBlock', () => {
  let block: DataMongoBlock;
  let area: AreaPlugin<any, any>;
  let injector: Injector;
  let mockDatasetService: any;
  let datasetService: any;
  let mockWorkflowEditor: any;

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
      getDfContentDataset: jasmine.createSpy('getDfContentDataset'),
      getContentDataset: jasmine.createSpy('getContentDataset')
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
    mockWorkflowEditor = {
      injector,
      getConnections: jasmine.createSpy('getConnections').and.returnValue([]),
      removeConnection: jasmine.createSpy('removeConnection')
    };

    Object.defineProperty(area, 'parent', {
      value: mockWorkflowEditor,
      writable: true,
      configurable: true
    });

    block = new DataMongoBlock('label', area);
    datasetService = jasmine.createSpyObj('DatasetService', ['datasets', 'getDfContentDataset', 'getContentDataset']);
    block['datasetService'] = datasetService;
  });

  it('should create an instance', () => {
    expect(block).toBeTruthy();
  });

  it('should create output and update status', () => {
    spyOn(area, 'update');

    block.createOutput({} as any, 'db', 'mytable', 'dataset-id');

    expect(block.dataOutput.get('out')).toEqual({} as any);
    expect(block.status).toBe(2); // StatusNode.Complete is 2
    expect(area.update).toHaveBeenCalledWith('node', block.id);
  });

  it('should clean output and remove connection when output exists', () => {
    spyOn(area, 'update');
    block.addOutput('out', new ClassicPreset.Output(new DeepObjectSocket(), 'out'));
    block.dataOutput.set('out', { some: 'data' } as any);
    mockWorkflowEditor.getConnections.and.returnValue([
      { source: block.id, sourceOutput: 'out', id: 'connection-1' }
    ]);

    block.cleanOutput();

    expect(mockWorkflowEditor.removeConnection).toHaveBeenCalledWith('connection-1');
    expect(block.outputs['out']).toBeUndefined();
    expect(block.dataOutput.has('out')).toBeFalse();
    expect(block.status).toBe(1); // StatusNode.Incomplete is 1
  });

  it('should add select collection control when content contains tables', () => {
    spyOn(area, 'update');
    const data = { collections: ['first', 'second'] } as any;

    block.addSelectCollection(data, {} as Node);

    expect(block.selectControlCollection).toBeDefined();
    expect(block.selectControlCollection.list.length).toBe(2);
    expect(area.update).toHaveBeenCalledWith('control', block.selectControlCollection.id);
  });

  it('should add select database control when content contains databases', () => {
    spyOn(area, 'update');
    const data = { databases: ['db1', 'db2'] } as any;

    block.addSelectDatabase(data, {} as Node);

    expect(block.selectControlDatabase).toBeDefined();
    expect(block.selectControlDatabase.list.length).toBe(2);
    expect(area.update).toHaveBeenCalledWith('control', block.selectControlDatabase.id);
  });

  it('should return merged node data', () => {
    block.selectControlDatabase = { value: 'db' } as any;
    block.selectControlCollection = { value: 'collection' } as any;

    const serialized = block.data();

    expect(serialized).toEqual(jasmine.objectContaining({
      selectDatabaseDataSource: block.selectControlDatabase,
      selectCollectionDataSource: block.selectControlCollection
    }));
  });

  it('should call getDfContentDataset when dataset has a collection', async () => {
    const event = { value: 'dataset-id', source: { writeValue: jasmine.createSpy() } } as any;
    const dataset = { id: 'dataset-id', database: 'db', collection: 'collection' } as any;
    block['selectControl'] = { value: 'dataset-id', oldValue: null } as any;
    datasetService.datasets.and.returnValue([dataset]);
    datasetService.getDfContentDataset.and.returnValue(of({ data: [] }));
    spyOn(block, 'createOutput');
    spyOn(area, 'update');

    await block.dataSourceChange(event as MatSelectChange);

    expect(datasetService.getDfContentDataset).toHaveBeenCalledWith(dataset, block.pagination, { database: 'db', table: 'collection' });
    expect(block.createOutput).toHaveBeenCalled();
  });

  it('should call getContentDataset when dataset has no collection', async () => {
    const event = { value: 'dataset-id', source: { writeValue: jasmine.createSpy() } } as any;
    const dataset = { id: 'dataset-id', database: null, collection: null } as any;
    block['selectControl'] = { value: 'dataset-id', oldValue: null } as any;
    datasetService.datasets.and.returnValue([dataset]);
    datasetService.getContentDataset.and.returnValue(of({ databases: ['db1'] }));
    spyOn(block, 'addSelectDatabase');
    spyOn(area, 'update');

    await block.dataSourceChange(event as MatSelectChange);

    expect(datasetService.getContentDataset).toHaveBeenCalledWith(dataset, block.pagination);
    expect(block.addSelectDatabase).toHaveBeenCalled();
  });
});
