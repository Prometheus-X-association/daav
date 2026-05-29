import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { TransformBlock } from './transform-block';
import { signal } from '@angular/core';
import { DatasetService } from 'src/app/services/dataset.service';
import { HttpClient } from '@angular/common/http';
import { TransformNodeComponent } from 'src/app/components/nodes/transform/nodes.component';

describe('TransformBlock', () => {
  let area: AreaPlugin<any, any>;
  let mockInjector: any;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);
    area.update = jasmine.createSpy('update');
    mockInjector = jasmine.createSpyObj('Injector', ['get']);
    (mockInjector.get as jasmine.Spy).and.callFake((token: any) => {
      if (token === DatasetService) {
        return { datasets: signal([]) };
      }
      if (token === HttpClient) {
        return jasmine.createSpyObj('HttpClient', ['get', 'post']);
      }
      return null;
    });
    Object.defineProperty(area, 'parent', {
      value: { injector: mockInjector },
      writable: true,
      configurable: true
    });
  });

  it('should create an instance', () => {
    const block = new TransformBlock('label', area);
    expect(block).toBeTruthy();
  });

  it('should add parquet checkbox and serialize data', () => {
    const block = new TransformBlock('label', area);
    expect(block['parquetCheckbox']).toBeDefined();
    expect(block.data()).toEqual(jasmine.objectContaining({ parquetSave: block['parquetCheckbox'] }));
  });

  it('should not throw on parquet save change', () => {
    const block = new TransformBlock('label', area);
    expect(() => block.parquetSaveChange({ value: true } as any)).not.toThrow();
  });

  it('should use provided node parquetSave data when present', () => {
    const node = { data: { parquetSave: { value: true, label: 'Parquet' } } } as any;
    const block = new TransformBlock('label', area, node);

    expect(block.parquetCheckbox).toBeDefined();
    expect(block.parquetCheckbox.value).toBeTrue();
    expect(block.data().parquetSave).toBe(block.parquetCheckbox);
    expect(area.update).toHaveBeenCalledWith('node', block.parquetCheckbox.id);
  });

  it('should return the transform node component and revision string', () => {
    const block = new TransformBlock('label', area);

    expect(block.getNodeComponent()).toBe(TransformNodeComponent);
    expect(block.getRevision()).toBe('123');
  });
});
