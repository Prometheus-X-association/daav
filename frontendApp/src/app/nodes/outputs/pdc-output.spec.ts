import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { PdcOutput } from './pdc-output';
import { Injector } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';

describe('PdcOutput', () => {
  let area: AreaPlugin<any, any>;
  let injector: Injector;
  let mockDatasetService: any;
  let httpClient: HttpClient;

  beforeEach(() => {
    mockDatasetService = {
      datasets: signal([]),
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
    httpClient = TestBed.inject(HttpClient);
    spyOn(httpClient, 'get').and.returnValue(of({ dataResources: [] }) as any);

    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
    Object.defineProperty(area, 'parent', {
      value: { injector },
      writable: true,
      configurable: true
    });
  });

  it('should create an instance', () => {
    const block = new PdcOutput('label', area);
    expect(block).toBeTruthy();
  });

  it('should format resource names to file names', () => {
    const block = new PdcOutput('label', area);
    expect(block['formatResourceNameAsFileName']('My Resource / File')).toBe('my-resource-file');
    expect(block['formatResourceNameAsFileName']('')).toBe('');
  });

  it('should add and remove select data resource control', () => {
    const block = new PdcOutput('label', area);
    spyOn(area, 'update');

    block['addSelectControlDataResource']({ dataResources: [{ name: 'Resource 1', _id: 'r1' }] });

    expect(block['selectControlDataResource']).toBeDefined();
    expect(block['selectControlDataResource'].list.length).toBe(1);

    block.removeControlDataSource();

    expect(block['selectControlDataResource']).toBeNull();
    expect(area.update).toHaveBeenCalledWith('node', block.id);
  });

  it('should process resource selection and add URL controls when URL exists', () => {
    const block = new PdcOutput('label', area);
    spyOn(area, 'update');
    block['dataResourcesResponse'] = {
      dataResources: [
        { _id: 'r1', name: 'Resource 1', representation: { url: 'https://example.com/file.csv' } }
      ]
    };
    block['selectControlDataResource'] = { value: 'r1' } as any;

    block['processDataResourceSelection']('r1');

    expect(block['currentUrlControl']).toBeDefined();
    expect(block['urlInputControl']).toBeDefined();
    expect(area.update).toHaveBeenCalled();
  });
});
