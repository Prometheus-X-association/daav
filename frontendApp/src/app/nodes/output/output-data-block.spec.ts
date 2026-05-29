import { AreaPlugin } from 'rete-area-plugin';
import { OutputDataBlock } from './output-data-block';
import { Schemes } from 'src/app/core/workflow-editor';
import { Injector } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';

describe('OutputDataBlock', () => {
  let area: AreaPlugin<any, any>;
  let injector: Injector;
  let mockDatasetService: any;

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
      getDatasets: jasmine.createSpy('getDatasets'),
      urlBack: 'https://api',
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
    const block = new OutputDataBlock('label', area);
    expect(block).toBeTruthy();
    expect(block.selectControl).toBeDefined();
  });

  it('should update source select result and preserve value when not inside list', () => {
    const block = new OutputDataBlock('label', area);
    spyOn(area, 'update');
    block['selectControl'] = { id: 'select-id', value: null, list: [], label: 'Dataset' } as any;

    block['updateSourceSelectResult']({ list: [{ label: 'Test', value: '1' }], idInside: false });

    expect(block.selectControl.list).toEqual([{ label: 'Test', value: '1' }]);
    expect(block.selectControl.value).toBeNull();
    expect(area.update).toHaveBeenCalledWith('control', block.selectControl.id);
  });

  it('should return data containing selectDataSource', () => {
    const block = new OutputDataBlock('label', area);
    expect(block.data()).toEqual(jasmine.objectContaining({ selectDataSource: block.selectControl }));
  });

  it('should filter dataset instances correctly', () => {
    const block = new OutputDataBlock('label', area);
    class DummyDataset {
      id = '1';
      name = 'dummy';
      description = '';
      type = '';
      dashboardComponent = null;
    }
    block['filterInputType'] = [DummyDataset];

    expect(block['datasetFilter'](new DummyDataset() as any)).toBeTrue();
  });
});
