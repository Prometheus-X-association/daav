import { AreaPlugin } from 'rete-area-plugin';
import { ApiOutput } from './api-output';
import { Schemes } from 'src/app/core/workflow-editor';
import { WorkflowNodeEditor } from 'src/app/core/workflow-node-editor';
import { Injector, signal } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';

describe('ApiOutput', () => {
  let area: AreaPlugin<any, any>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: DatasetService, useValue: { datasets: signal([]), getDatasets: jasmine.createSpy('getDatasets'), urlBack: 'https://api' } },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
      ]
    });
    const mockWorkflowEditor: Partial<WorkflowNodeEditor<Schemes>> = { injector: TestBed.inject(Injector) };

    area = new AreaPlugin<Schemes, never>(document.createElement('div'));
    area.update = jasmine.createSpy('update');
    Object.defineProperty(area, 'parent', { value: mockWorkflowEditor, writable: true, configurable: true });
  });

  function token(block: ApiOutput): string {
    return block['tokenControl'].value;
  }

  it('should generate a 64 character alphanumeric token', () => {
    expect(token(new ApiOutput('label', area))).toMatch(/^[A-Za-z0-9]{64}$/);
  });

  it('should generate a different token for each node', () => {
    expect(token(new ApiOutput('label', area))).not.toBe(token(new ApiOutput('label', area)));
  });

  it('should draw the token from the cryptographic generator', () => {
    const random = spyOn(Math, 'random').and.callThrough();
    const secureRandom = spyOn(crypto, 'getRandomValues').and.callThrough();

    new ApiOutput('label', area);

    expect(secureRandom).toHaveBeenCalled();
    expect(random).not.toHaveBeenCalled();
  });

  it('should pick every character with the same probability', () => {
    // 248 and above would favour the first characters of the alphabet: these bytes are drawn again
    let call = 0;
    spyOn(crypto, 'getRandomValues').and.callFake(<T extends ArrayBufferView | null>(array: T): T => {
      (array as unknown as Uint8Array).fill(call++ === 0 ? 255 : 61);
      return array;
    });

    expect(token(new ApiOutput('label', area))).toBe('9'.repeat(64));
  });

  it('should keep the token of a saved node', () => {
    const saved = { value: 'saved-token', list: [], label: 'Enter the token', type: 'password', showPassword: false };
    const block = new ApiOutput('label', area, { id: 'n1', data: { tokenInput: saved }, inputs: {}, outputs: {} } as any);

    expect(token(block)).toBe('saved-token');
  });
});
