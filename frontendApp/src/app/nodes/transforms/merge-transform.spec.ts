import { MergeTransform } from './merge-transform';
import { AreaPlugin } from 'rete-area-plugin';
import { Node } from 'src/app/models/interfaces/node';
import { StatusNode } from 'src/app/enums/status-node';
import { DataMapperControl } from 'src/app/components/widgets/data-mapper-widget/data-mapper-widget.component';
import { Schemes } from 'src/app/core/workflow-editor';
import { ClassicPreset } from 'rete';
import { AllSocket } from 'src/app/core/sockets/sockets';


describe('MergeTransform', () => {
  let area: AreaPlugin<any, any>;

  beforeEach(() => {
    const container = document.createElement('div');
    area = new AreaPlugin<Schemes, never>(container);

    // Améliorer le mock avec plus de détails
    area.parent = {
      getNode: jasmine.createSpy('getNode').and.returnValue({
        label: 'Test Node',
        data: { output: ['someData'] }
      }),
      getConnections: jasmine.createSpy('getConnections').and.returnValue([])
    };
  });

  it('should create an instance', () => {
    const instance = new MergeTransform('Test Label', area);
    expect(instance).toBeTruthy();
  });

  it('should initialize with default values when no node is provided', () => {
    const instance = new MergeTransform('Test Label', area);
    expect(instance.width).toBe(350); // MergeTransform has width 350
    expect(instance.height).toBe(192);
    expect(instance.dataMapperControl).toBeInstanceOf(DataMapperControl);
    expect(instance.dataMapperControl.mappings).toEqual([]);
    expect(instance.dataMapperControl.datasets).toEqual([]);
  });

  it('should initialize with node data when node is provided', () => {
    const node: Node = {
      id: '1',
      data: {
        dataMapping: [{ source: 'source1', target: 'target1' }],
        datasets: ['dataset1']
      }
    } as Node;
    const instance = new MergeTransform('Test Label', area, node);
    expect(instance.dataMapperControl.mappings).toEqual(node.data.dataMapping);
    expect(instance.dataMapperControl.datasets).toEqual(node.data.datasets);
  });

  it('should update status to Incomplete when no node is provided', () => {
    const instance = new MergeTransform('Test Label', area);
    expect(instance.status).toBe(StatusNode.Incomplete);
  });

  it('should add input and output on connection created', () => {
    const instance = new MergeTransform('Test Label', area);
    const connection = {
      source: 'sourceNode',
      sourceOutput: 'output1',
      target: instance.id,
      targetInput: 'datasource'
    } as any;

    // Mock getNode to return a node with proper data structure
    (area.parent.getNode as jasmine.Spy).and.returnValue({
      label: 'Source Node',
      id: 'sourceNode',
      outputs: {
        output1: { socket: {} }
      },
      data: {
        output: ['someData']
      },
      dataOutput: new Map([['output1', ['data']]])
    });

    instance['onConnectionChange'](connection, 'connectioncreated');
    expect(Object.keys(instance.inputs)).toContain('datasource_1');
    expect(Object.keys(instance.outputs)).toContain('out');
  });

  it('should remove input and output on connection removed', () => {
    const instance = new MergeTransform('Test Label', area);
    const connection = {
      id: 'connection1',
      source: 'sourceNode',
      sourceOutput: 'output1',
      target: instance.id,
      targetInput: 'datasource'
    };

    // Mock getNode with complete data
    (area.parent.getNode as jasmine.Spy).and.returnValue({
      label: 'Source Node',
      id: 'sourceNode',
      outputs: {
        output1: { socket: {} }
      },
      data: {
        output: ['someData']
      },
      dataOutput: new Map([['output1', ['data']]])
    });

    instance['onConnectionChange'](connection, 'connectioncreated');
    instance['onConnectionChange'](connection, 'connectionremoved');
    expect(Object.keys(instance.inputs)).not.toContain('datasource_1');
    expect(Object.keys(instance.outputs)).not.toContain('out');
  });

  it('should build dataset on connection created', () => {
    const instance = new MergeTransform('Test Label', area);
    const mockSchema = {
      fields: [{ name: 'field1', type: { toString: () => 'string' } }]
    };
    const mockSourceNode = {
      label: 'Source Node',
      id: 'sourceNode',
      data: {
        output: ['someData']
      },
      dataOutput: new Map([['output1', {
        type: 'parquet',
        name: 'Test Dataset',
        data: [{ field1: 'value1' }],
        schema: mockSchema,
        nodeSchema: mockSchema,
        dataExample: { field1: ['value1'] }
      }]]),
      schema: new Map([['output1', mockSchema]])
    };

    const mockConnection = {
      source: 'sourceNode',
      target: instance.id,
      targetInput: 'datasource',
      sourceOutput: 'output1'
    };

    (area.parent.getNode as jasmine.Spy).and.returnValue(mockSourceNode);
    (area.parent.getConnections as jasmine.Spy).and.returnValue([mockConnection]);

    instance['buildDataset']('connectioncreated');
    expect(instance.dataMapperControl.datasets.length).toBeGreaterThan(0);
  });

  it('should clear datasets and mappings on connection removed', () => {
    const instance = new MergeTransform('Test Label', area);
    instance['buildDataset']('connectionremoved');
    expect(instance.dataMapperControl.datasets).toEqual([]);
    expect(instance.dataMapperControl.mappings).toEqual([]);
  });
  describe('onConnectionChange', () => {
    let instance: MergeTransform;
    let connections: any[];

    function addInputs(...indexes: number[]) {
      indexes.forEach(index => instance.addInput(`datasource_${index}`, new ClassicPreset.Input(new AllSocket(), `DataSource ${index}`)));
    }

    function change(targetInput: string, type: 'connectioncreated' | 'connectionremoved') {
      instance['onConnectionChange']({ id: `c-${targetInput}`, source: 'sourceNode', sourceOutput: 'output1', target: instance.id, targetInput } as any, type);
    }

    beforeEach(() => {
      connections = [];
      area.parent.getConnections = jasmine.createSpy('getConnections').and.callFake(() => connections);
      area.parent.removeConnection = jasmine.createSpy('removeConnection');
      instance = new MergeTransform('Test Label', area);
      spyOn<any>(instance, 'buildDataset');
    });

    it('should create the next input when an indexed input is connected', () => {
      addInputs(1, 2);
      const socket = instance.inputs['datasource_2'].socket;

      change('datasource_2', 'connectioncreated');

      expect(Object.keys(instance.inputs)).toEqual(['datasource', 'datasource_1', 'datasource_2', 'datasource_3']);
      expect(instance.inputs['datasource_3'].socket).toBe(socket);
      expect(instance.inputs['datasource_3'].label).toBe('DataSource 3');
      expect(instance['buildDataset']).toHaveBeenCalledWith('connectioncreated');
    });

    it('should not create the next input twice', () => {
      addInputs(1, 2);
      const existing = instance.inputs['datasource_2'];

      change('datasource_1', 'connectioncreated');

      expect(Object.keys(instance.inputs)).toEqual(['datasource', 'datasource_1', 'datasource_2']);
      expect(instance.inputs['datasource_2']).toBe(existing);
    });

    it('should create the first indexed input with the primary socket when the source node is unknown', () => {
      (area.parent.getNode as jasmine.Spy).and.returnValue(undefined);
      const socket = instance.inputs['datasource'].socket;

      change('datasource', 'connectioncreated');

      expect(Object.keys(instance.inputs)).toEqual(['datasource', 'datasource_1']);
      expect(instance.inputs['datasource_1'].socket).toBe(socket);
      expect(instance.inputs['datasource_1'].label).toBe('DataSource 1');
      expect(Object.keys(instance.outputs)).toEqual([]);
    });

    it('should remove the next input when it is not connected', () => {
      addInputs(1, 2);

      change('datasource_1', 'connectionremoved');

      expect(Object.keys(instance.inputs)).toEqual(['datasource', 'datasource_1']);
      expect(instance['buildDataset']).toHaveBeenCalledWith('connectionremoved');
    });

    it('should keep the next input when it is connected', () => {
      addInputs(1, 2);
      connections = [{ id: 'c2', target: instance.id, targetInput: 'datasource_2' }];

      change('datasource_1', 'connectionremoved');

      expect(Object.keys(instance.inputs)).toEqual(['datasource', 'datasource_1', 'datasource_2']);
    });

    it('should remove the disconnected input above 1 when the previous input is free', () => {
      addInputs(1, 2, 3);

      change('datasource_2', 'connectionremoved');

      expect(Object.keys(instance.inputs)).toEqual(['datasource', 'datasource_1']);
    });

    it('should keep the disconnected input above 1 when the previous input is connected', () => {
      addInputs(1, 2, 3);
      connections = [
        { id: 'c1', target: instance.id, targetInput: 'datasource_1' },
        { id: 'c3', target: instance.id, targetInput: 'datasource_3' }
      ];

      change('datasource_2', 'connectionremoved');

      expect(Object.keys(instance.inputs)).toEqual(['datasource', 'datasource_1', 'datasource_2', 'datasource_3']);
    });

    it('should remove the other inputs, their connections and the output when the primary input is disconnected', () => {
      addInputs(1, 2);
      instance.addOutput('out', new ClassicPreset.Output(new AllSocket(), 'Out'));
      connections = [
        { id: 'c1', target: instance.id, targetInput: 'datasource_1' },
        { id: 'c-out', source: instance.id, sourceOutput: 'out', target: 'next' }
      ];

      change('datasource', 'connectionremoved');

      expect(Object.keys(instance.inputs)).toEqual(['datasource']);
      expect(Object.keys(instance.outputs)).toEqual([]);
      expect(area.parent.removeConnection).toHaveBeenCalledWith('c1');
      expect(area.parent.removeConnection).toHaveBeenCalledWith('c-out');
      expect(instance['buildDataset']).toHaveBeenCalledWith('connectionremoved');
    });

    it('should ignore inputs that are not data sources', () => {
      instance.addInput('other', new ClassicPreset.Input(new AllSocket(), 'Other'));

      change('other', 'connectioncreated');

      expect(Object.keys(instance.inputs)).toEqual(['datasource', 'other']);
      expect(instance['buildDataset']).toHaveBeenCalledWith('connectioncreated');
    });
  });
});
