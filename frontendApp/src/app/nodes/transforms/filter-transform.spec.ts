import { AreaPlugin } from 'rete-area-plugin';
import { Schemes } from 'src/app/core/workflow-editor';
import { FilterTransform } from './filter-transform';
import { Node } from 'src/app/models/interfaces/node';
import { StatusNode } from 'src/app/enums/status-node';

describe('FilterTransform', () => {
  let area: AreaPlugin<any, any>;
  let workflowParent: any;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);

    workflowParent = {
      getNode: jasmine.createSpy('getNode'),
      getConnections: jasmine.createSpy('getConnections').and.returnValue([]),
      removeConnection: jasmine.createSpy('removeConnection')
    };

    Object.defineProperty(area, 'parent', {
      value: workflowParent,
      writable: true,
      configurable: true
    });
  });

  it('should create an instance', () => {
    const block = new FilterTransform('label', area);
    expect(block).toBeTruthy();
  });

  it('should add output when datasource connection is created', () => {
    const sourceNode: any = {
      outputs: {
        output1: { socket: { type: 'socket' } }
      }
    };
    workflowParent.getNode.and.returnValue(sourceNode);
    const block = new FilterTransform('label', area);

    block['onConnectionChange']({ source: 'source1', sourceOutput: 'output1', target: block.id, targetInput: 'datasource' } as any, 'connectioncreated');

    expect(Object.keys(block.outputs)).toContain('out');
  });

  it('should remove output when datasource connection is removed', () => {
    const sourceNode: any = {
      outputs: {
        output1: { socket: { type: 'socket' } }
      }
    };
    workflowParent.getNode.and.returnValue(sourceNode);

    const block = new FilterTransform('label', area);
    block['addOutput']('out', { socket: {} } as any);
    workflowParent.getConnections.and.returnValue([{ source: block.id, sourceOutput: 'out', id: 'out-conn' }]);

    block['onConnectionChange']({ source: 'source1', sourceOutput: 'output1', target: block.id, targetInput: 'datasource' } as any, 'connectionremoved');

    expect(block.outputs['out']).toBeUndefined();
    expect(workflowParent.removeConnection).toHaveBeenCalledWith('out-conn');
  });

  it('should build dataset when a connection exists', () => {
    const nodeData = {
      type: 'pandasdf',
      name: 'Test Dataset',
      nodeSchema: [{ name: 'field1', dtype: 'object' }],
      dataExample: { field1: ['value1'] }
    };
    const sourceNode: any = {
      dataOutput: new Map([['output1', nodeData]])
    };
    workflowParent.getNode.and.returnValue(sourceNode);
    workflowParent.getConnections.and.returnValue([{ target: 'filter1', targetInput: 'datasource', source: 'source1', sourceOutput: 'output1' }]);

    const block = new FilterTransform('label', area);
    block['id'] = 'filter1';

    block['buildDataset']('connectioncreated');

    expect(block['dataFilterControl'].datasets.length).toBe(1);
    expect(block.data().dataSource).toBe('datasource');
  });

  it('should reset query when connection removed', () => {
    const block = new FilterTransform('label', area);
    block['dataFilterControl'].query = { condition: 'and', rules: [{ field: 'x' }] } as any;
    workflowParent.getConnections.and.returnValue([]);

    block['buildDataset']('connectionremoved');

    expect(block['dataFilterControl'].datasets).toEqual([]);
    expect(block['dataFilterControl'].query).toEqual({ condition: 'and', rules: [] });
  });

  it('should initialize with provided node dataset, filter rules and dataSource', () => {
    const node: any = {
      data: {
        datasets: [{ id: 'd1' }],
        filterRules: { condition: 'and', rules: [{ field: 'x' }] },
        dataSource: 'datasource'
      }
    };
    const block = new FilterTransform('label', area, node);

    expect(block['dataFilterControl'].datasets).toEqual(node.data.datasets);
    expect(block['dataFilterControl'].query).toEqual(node.data.filterRules);
    expect(block['dataSource']).toBe('datasource');
  });

  it('should not call onConnectionChange during clear context', () => {
    const beforeCount = (area as any).signal.pipes.length;
    const block = new FilterTransform('label', area);
    const pipe = (area as any).signal.pipes[(area as any).signal.pipes.length - 1];
    const spy = spyOn(block as any, 'onConnectionChange').and.callThrough();

    pipe({ type: 'clear' });
    pipe({
      type: 'connectioncreated',
      data: { source: 'source1', sourceOutput: 'output1', target: block.id, targetInput: 'datasource' }
    });

    expect(spy).not.toHaveBeenCalled();
    expect((area as any).signal.pipes.length).toBeGreaterThanOrEqual(beforeCount + 1);
  });

  it('should remove its pipe when node is removed', () => {
    const beforeCount = (area as any).signal.pipes.length;
    const block = new FilterTransform('label', area);
    const pipe = (area as any).signal.pipes[(area as any).signal.pipes.length - 1];

    pipe({ type: 'noderemoved', data: { id: block.id } });

    expect((area as any).signal.pipes.length).toBeLessThan(beforeCount + 1);
  });

  it('should build dataset on nodeDataOutputUpdated when there is an incoming connection', () => {
    const beforeCount = (area as any).signal.pipes.length;
    const block = new FilterTransform('label', area);
    block.id = 'filter1';

    const incomingConnection = { target: block.id, source: 'source1', sourceOutput: 'output1', targetInput: 'datasource' };
    workflowParent.getConnections.and.returnValue([incomingConnection]);
    const spy = spyOn(block as any, 'buildDataset').and.callThrough();

    const pipe = (area as any).signal.pipes[(area as any).signal.pipes.length - 1];
    pipe({ type: 'nodeDataOutputUpdated', data: { nodeId: 'source1', outputKey: 'output1' } });

    expect(spy).toHaveBeenCalledWith('nodeDataOutputUpdated');
    expect((area as any).signal.pipes.length).toBeGreaterThanOrEqual(beforeCount + 1);
  });

  it('should set status to Complete when filter rules exist on close', () => {
    const block = new FilterTransform('label', area);
    block['dataFilterControl'].query = { condition: 'and', rules: [{ field: 'x' }] } as any;

    block.onFilterClose();

    expect(block.status).toBe(StatusNode.Complete);
  });

  it('should serialize filter data correctly', () => {
    const block = new FilterTransform('label', area);
    block['dataFilterControl'].query = { condition: 'and', rules: [] } as any;
    block['dataFilterControl'].datasets = [{ id: 'd1', name: 'Data', columns: [] } as any];
    block['dataSource'] = 'datasource';

    const serialized = block.data();

    expect(serialized).toEqual(jasmine.objectContaining({
      datasets: block['dataFilterControl'].datasets,
      filterRules: block['dataFilterControl'].query,
      dataSource: 'datasource'
    }));
  });

  it('should set status to Incomplete when filter rules are empty on close', () => {
    const block = new FilterTransform('label', area);
    block['dataFilterControl'].query = { condition: 'and', rules: [] } as any;

    block.onFilterClose();

    expect(block.status).toBe(1);
  });
});
