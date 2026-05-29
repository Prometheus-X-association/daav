import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { InputDataBlock } from './input-data-block';
import { Injector } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { MatSelectChange } from '@angular/material/select';

describe('InputDataBlock', () => {
  let area: AreaPlugin<any, any>;
  let injector: Injector;
  let mockDatasetService: any;
  let mockWorkflowEditor: any;

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
    mockWorkflowEditor = {
      injector,
      getConnections: jasmine.createSpy('getConnections').and.returnValue([])
    };

    Object.defineProperty(area, 'parent', {
      value: mockWorkflowEditor,
      writable: true,
      configurable: true
    });
  });

  it('should create an instance', () => {
    expect(new InputDataBlock('label', area)).toBeTruthy();
  });

  it('should initialize selectControl and parquetCheckbox', () => {
    const block = new InputDataBlock('label', area);

    expect(block.selectControl).toBeDefined();
    expect(block.parquetCheckbox).toBeDefined();
    expect(block.selectControl.value).toBeNull();
  });

  it('should return serialized data with select and parquet controls', () => {
    const block = new InputDataBlock('label', area);
    block.selectControl = { value: 'dataset-1' } as any;
    block.parquetCheckbox = { value: true } as any;

    const result = block.data();

    expect(result).toEqual(jasmine.objectContaining({
      selectDataSource: block.selectControl,
      parquetSave: block.parquetCheckbox,
    }));
  });

  it('should detect connected output when workflow editor has a connection for this node', () => {
    const block = new InputDataBlock('label', area);
    mockWorkflowEditor.getConnections.and.returnValue([{ source: block.id }]);

    expect(block.haveOuputConnected()).toBeTrue();
  });

  it('should confirm source change when no output connection exists', async () => {
    const block = new InputDataBlock('label', area);
    const event = { value: null, source: { writeValue: jasmine.createSpy() } } as unknown as MatSelectChange<any>;

    const result = await block.confirmChangeSource(event);

    expect(result).toBeTrue();
    expect(event.source.writeValue).not.toHaveBeenCalled();
  });

  it('should restore select control old value when source change is cancelled', async () => {
    const block = new InputDataBlock('label', area);
    block.selectControl = { value: 'dataset-2', oldValue: 'dataset-old' } as any;
    mockWorkflowEditor.getConnections.and.returnValue([{ source: block.id }]);
    spyOn(block, 'popAlert').and.resolveTo(false);

    const event = { value: null, source: { writeValue: jasmine.createSpy() } } as unknown as MatSelectChange<any>;
    const result = await block.confirmChangeSource(event);

    expect(result).toBeFalse();
    expect(event.source.writeValue).toHaveBeenCalledWith('dataset-old');
    expect(block.selectControl.value).toBe('dataset-old');
  });
});
