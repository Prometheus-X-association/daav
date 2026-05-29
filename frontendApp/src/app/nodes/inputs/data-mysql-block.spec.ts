import { ClassicPreset } from 'rete';
import { DataMysqlBlock } from './data-mysql-block';
import { AreaPlugin } from 'rete-area-plugin';
import { Node } from 'src/app/models/interfaces/node';
import { MatSelectChange } from '@angular/material/select';
import { DatasetService } from 'src/app/services/dataset.service';
import { of } from 'rxjs';
import { Injector } from '@angular/core';
import { FlatObjectSocket } from 'src/app/core/sockets/sockets';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';

describe('DataMysqlBlock', () => {
  let block: DataMysqlBlock;
  let area: AreaPlugin<any, any>;
  let node: Node;
  let datasetService: DatasetService;
  let injector: Injector;
  let mockDatasetService: any;
  let mockWorkflowEditor: any;

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
      getDatasets: jasmine.createSpy('getDatasets'),
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
    area = new AreaPlugin(container);
    node = { data: {} } as Node;
    datasetService = jasmine.createSpyObj('DatasetService', ['datasets', 'getContentDataset']);

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

    block = new DataMysqlBlock('Test Block', area, node);
    block['datasetService'] = datasetService;
  });

  it('should create an instance', () => {
    expect(block).toBeTruthy();
  });

  it('should handle dataSourceChange', async () => {
    const event = { value: 'test-dataset-id', source: { writeValue: jasmine.createSpy() } } as any;
    const dataset = { id: 'test-dataset-id', database: 'test-db', table: 'test-table' } as any;

    // Initialize selectControl
    block['selectControl'] = { value: 'test-dataset-id', oldValue: null } as any;

    spyOn(block, 'cleanOutput');
    spyOn(block, 'removeControlDatabase');
    spyOn(block, 'removeControlTable');
    spyOn(block, 'showLoader');
    spyOn(block, 'createOutput');
    spyOn(block, 'addSelectTable');
    spyOn(block, 'addSelectDatabase');
    (datasetService.datasets as unknown as jasmine.Spy).and.returnValue([dataset]);
    (datasetService.getContentDataset as jasmine.Spy).and.returnValue(of({ data: [], table_description: {}, tables: [], databases: [] }));

    await block.dataSourceChange(event);

    expect(block.cleanOutput).toHaveBeenCalled();
    expect(block.removeControlDatabase).toHaveBeenCalled();
    expect(block.removeControlTable).toHaveBeenCalled();
    expect(block.showLoader).toHaveBeenCalledWith(true);
    expect(datasetService.getContentDataset).toHaveBeenCalledWith(dataset, block.pagination);
  });

  it('should handle dataBaseChange', () => {
    const event = { value: 'test-db' } as MatSelectChange;
    const dataset = { id: 'test-dataset-id' } as any;

    // Initialize selectControl
    block['selectControl'] = { value: 'test-dataset-id' } as any;

    spyOn(block, 'removeControlTable');
    spyOn(block, 'cleanOutput');
    spyOn(block, 'showLoader');
    spyOn(block, 'addSelectTable');
    (datasetService.datasets as unknown as jasmine.Spy).and.returnValue([dataset]);
    (datasetService.getContentDataset as jasmine.Spy).and.returnValue(of({ data: [], table_description: {}, tables: [], databases: [] }));

    block.dataBaseChange(event);

    expect(block.removeControlTable).toHaveBeenCalled();
    expect(block.cleanOutput).toHaveBeenCalled();
    expect(block.showLoader).toHaveBeenCalledWith(true);
    expect(datasetService.getContentDataset).toHaveBeenCalledWith(dataset, block.pagination, { database: event.value, table: null });
  });

  it('should handle tableChange', () => {
    const event = { value: 'test-table' } as MatSelectChange;
    const dataset = { id: 'test-dataset-id', database: 'test-db' } as any;

    // Initialize selectControl and selectControlDatabase
    block['selectControl'] = { value: 'test-dataset-id' } as any;
    block['selectControlDatabase'] = { value: 'test-db' } as any;

    spyOn(block, 'cleanOutput');
    spyOn(block, 'showLoader');
    spyOn(block, 'createOutput');
    (datasetService.datasets as unknown as jasmine.Spy).and.returnValue([dataset]);
    (datasetService.getContentDataset as jasmine.Spy).and.returnValue(of({ data: [], table_description: {}, tables: [], databases: [] }));

    block.tableChange(event);

    expect(block.cleanOutput).toHaveBeenCalled();
    expect(block.showLoader).toHaveBeenCalledWith(true);
    expect(datasetService.getContentDataset).toHaveBeenCalledWith(dataset, block.pagination, { database: 'test-db', table: event.value });
  });

  it('should return correct data', () => {
    block.selectControlDatabase = { value: 'test-db' } as any;
    block.selectControlTable = { value: 'test-table' } as any;

    const data = block.data();

    expect(data).toEqual(jasmine.objectContaining({
      selectDatabaseDataSource: block.selectControlDatabase,
      selectTableDataSource: block.selectControlTable,
    }));
  });

  it('should create output and update status', () => {
    spyOn(area, 'update');
    block.createOutput({ data: [] } as any, 'db', 'table', 'dataset-id');

    expect(block.dataOutput.get('out')).toEqual(jasmine.objectContaining({
      datasetId: 'dataset-id',
      database: 'db',
      table: 'table',
    }));
    expect(block.status).toBe(2);
    expect(area.update).toHaveBeenCalledWith('node', block.id);
  });

  it('should clean output and remove connection when output exists', () => {
    spyOn(area, 'update');
    block.addOutput('out', new ClassicPreset.Output(new FlatObjectSocket(), 'out'));
    block.dataOutput.set('out', { some: 'data' } as any);
    mockWorkflowEditor.getConnections.and.returnValue([
      { source: block.id, sourceOutput: 'out', id: 'conn-1' }
    ]);

    block.cleanOutput();

    expect(mockWorkflowEditor.removeConnection).toHaveBeenCalledWith('conn-1');
    expect(block.outputs['out']).toBeUndefined();
    expect(block.dataOutput.has('out')).toBeFalse();
    expect(block.status).toBe(1);
  });

  it('should add select table control from tables list', () => {
    spyOn(area, 'update');
    const data = { tables: ['t1', 't2'] } as any;

    block.addSelectTable(data, {} as Node);

    expect(block.selectControlTable).toBeDefined();
    expect(block.selectControlTable.list.length).toBe(2);
    expect(area.update).toHaveBeenCalledWith('control', block.selectControlTable.id);
  });

  it('should add select database control from databases list', () => {
    spyOn(area, 'update');
    const data = { databases: ['db1', 'db2'] } as any;

    block.addSelectDatabase(data, {} as Node);

    expect(block.selectControlDatabase).toBeDefined();
    expect(block.selectControlDatabase.list.length).toBe(2);
    expect(area.update).toHaveBeenCalledWith('control', block.selectControlDatabase.id);
  });

  it('should remove control database and clear saved table import state', () => {
    const node = { data: { selectTableDataSource: { value: null } } } as any;
    block['node'] = node;
    block.selectControlDatabase = { id: 'dataDatabaseSource' } as any;

    block.removeControlDatabase();

    expect(block.selectControlDatabase).toBeNull();
    expect(node.data.selectTableDataSource).toBeNull();
  });

  it('should remove control table and clear saved table import state', () => {
    const node = { data: { selectTableDataSource: { value: null } } } as any;
    block['node'] = node;
    block.selectControlTable = { id: 'dataTableSource' } as any;

    block.removeControlTable();

    expect(block.selectControlTable).toBeNull();
    expect(node.data.selectTableDataSource).toBeNull();
  });
});

