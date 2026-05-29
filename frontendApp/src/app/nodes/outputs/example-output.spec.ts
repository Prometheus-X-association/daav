import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { ExampleOutput } from './example-output';
import { Injector } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient, provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';

describe('ExampleOutput', () => {
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
    expect(new ExampleOutput('label',area)).toBeTruthy();
  });

  it('should add expected inputs when created without node', () => {
    const block = new ExampleOutput('label', area);

    expect(Object.keys(block.inputs)).toContain('oneColonne');
    expect(Object.keys(block.inputs)).toContain('flatObject');
    expect(block.status).toBe(1); // Incomplete
  });
});
