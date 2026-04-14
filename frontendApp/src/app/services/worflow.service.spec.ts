import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { WorkflowService } from './worflow.service';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('WorflowService', () => {
  let service: WorkflowService;

  beforeEach(() => {
    TestBed.configureTestingModule({
    imports: [],
    providers: [provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()]
});
    service = TestBed.inject(WorkflowService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
