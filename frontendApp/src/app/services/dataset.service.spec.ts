import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { DatasetService } from './dataset.service';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('DatasetService', () => {
  let service: DatasetService;

  beforeEach(() => {
    TestBed.configureTestingModule({
    imports: [],
    providers: [provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()]
});
    service = TestBed.inject(DatasetService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
