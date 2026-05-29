import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { DataFileBlock } from './data-file-block';
import { Injector } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';

describe('DataFileBlock', () => {
  let area: AreaPlugin<any, any>;
  let injector: Injector;
  let mockDatasetService: any;

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
      getDatasets: jasmine.createSpy('getDatasets')
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

    Object.defineProperty(area, 'parent', {
      value: { injector },
      writable: true,
      configurable: true
    });
  });

  it('should create an instance', () => {
    expect(new DataFileBlock('label',area)).toBeTruthy();
  });

  it('should create output and update status', () => {
    const block = new DataFileBlock('label', area);
    spyOn(area, 'update');

    const data = { name: 'file', nodeSchema: [{ name: 'col1', dtype: 'object', nullable: false }], data: [] } as any;
    block.createOutput(data);

    expect(block.dataOutput.get('out')).toBe(data);
    expect(block.status).toBe(2);
    expect(area.update).toHaveBeenCalledWith('node', block.id);
  });

  it('should clean output and remove connection if connected', () => {
    const mockWorkflowEditor = {
      injector,
      getConnections: jasmine.createSpy('getConnections'),
      removeConnection: jasmine.createSpy('removeConnection')
    };
    Object.defineProperty(area, 'parent', {
      value: mockWorkflowEditor,
      writable: true,
      configurable: true
    });

    const block = new DataFileBlock('label', area);
    mockWorkflowEditor.getConnections.and.returnValue([{
      source: block.id,
      sourceOutput: 'out',
      id: 'conn-2'
    }]);
    spyOn(area, 'update');
    block.addOutput('out', {} as any);
    block.dataOutput.set('out', { fileData: true } as any);

    block.cleanOutput();

    expect(mockWorkflowEditor.removeConnection).toHaveBeenCalledWith('conn-2');
    expect(block.outputs['out']).toBeUndefined();
    expect(block.dataOutput.has('out')).toBeFalse();
    expect(block.status).toBe(1);
  });
});
