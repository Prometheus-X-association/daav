import { WorkflowEditor } from './workflow-editor';
import { Injector, EnvironmentInjector } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Project } from '../models/interfaces/project';
import { WorkflowService } from '../services/worflow.service';
import { of } from 'rxjs';
import { ClassicPreset } from 'rete';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('WorkflowEditor', () => {
  let injector: Injector;
  let mockWorkflowService: jasmine.SpyObj<WorkflowService>;
  let workflowEditorInstance: WorkflowEditor | null = null;

  beforeEach(() => {
    mockWorkflowService = jasmine.createSpyObj('WorkflowService', ['executeNodeJson', 'saveProject']);

    TestBed.configureTestingModule({
    teardown: { destroyAfterEach: false } // Prevent TestBed from destroying injector
    ,
    imports: [],
    providers: [
        { provide: WorkflowService, useValue: mockWorkflowService },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
    ]
});

    injector = TestBed.inject(Injector);
  });

  afterEach(() => {
    // Clean up workflow editor instance but don't destroy TestBed injector
    if (workflowEditorInstance) {
      workflowEditorInstance = null;
    }
  });

  function createWorkflowEditor(): WorkflowEditor {
    const container = document.createElement('div');
    workflowEditorInstance = new WorkflowEditor(container, injector);
    return workflowEditorInstance;
  }

  describe('Static Methods (No DOM needed)', () => {
    it('should create socketFactory for SimpleFieldSocket', () => {
      const workflowEditor = createWorkflowEditor();

      const socket = workflowEditor['socketFactory']('SimpleFieldSocket');
      expect(socket).toBeDefined();
      expect(socket.name).toBe('SimpleFieldSocket');
    });

    it('should create socketFactory for LrsObjectSocket', () => {
      const workflowEditor = createWorkflowEditor();

      const socket = workflowEditor['socketFactory']('LrsObjectSocket');
      expect(socket).toBeDefined();
      expect(socket.name).toBe('LrsObjectSocket');
    });

    it('should create socketFactory for DeepObjectSocket', () => {
      const workflowEditor = createWorkflowEditor();

      const socket = workflowEditor['socketFactory']('DeepObjectSocket');
      expect(socket).toBeDefined();
      expect(socket.name).toBe('DeepObjectSocket');
    });

    it('should create socketFactory for FlatObjectSocket', () => {
      const workflowEditor = createWorkflowEditor();

      const socket = workflowEditor['socketFactory']('FlatObjectSocket');
      expect(socket).toBeDefined();
      expect(socket.name).toBe('FlatObjectSocket');
    });

    it('should create socketFactory for AllSocket', () => {
      const workflowEditor = createWorkflowEditor();

      const socket = workflowEditor['socketFactory']('AllSocket');
      expect(socket).toBeDefined();
      expect(socket.name).toBe('AllSocket');
    });

    it('should create generic socket for unknown types', () => {
      const workflowEditor = createWorkflowEditor();

      const socket = workflowEditor['socketFactory']('CustomSocket');
      expect(socket).toBeDefined();
      expect(socket).toBeInstanceOf(ClassicPreset.Socket);
    });

    it('should serialize input port', () => {
      const workflowEditor = createWorkflowEditor();

      const socket = new ClassicPreset.Socket('TestSocket');
      const input = new ClassicPreset.Input(socket, 'Test Input');
      input.id = 'input-1';

      const serialized = workflowEditor['serializePort'](input);

      expect(serialized).toEqual({
        id: 'input-1',
        label: 'Test Input',
        socket: { name: 'TestSocket' }
      });
    });

    it('should serialize output port', () => {
      const workflowEditor = createWorkflowEditor();

      const socket = new ClassicPreset.Socket('TestSocket');
      const output = new ClassicPreset.Output(socket, 'Test Output');
      output.id = 'output-1';

      const serialized = workflowEditor['serializePort'](output);

      expect(serialized).toEqual({
        id: 'output-1',
        label: 'Test Output',
        socket: { name: 'TestSocket' }
      });
    });

    it('should serialize InputControl', () => {
      const workflowEditor = createWorkflowEditor();

      const control = new ClassicPreset.InputControl('text', {
        initial: 'test value',
        readonly: false
      });
      control.id = 'control-1';

      const serialized = workflowEditor['serializeControl'](control);

      expect(serialized).toEqual({
        __type: 'ClassicPreset.InputControl',
        id: 'control-1',
        readonly: false,
        type: 'text',
        value: 'test value'
      });
    });

    it('should return null for unknown control types', () => {
      const workflowEditor = createWorkflowEditor();

      const customControl = {} as any;

      const serialized = workflowEditor['serializeControl'](customControl);

      expect(serialized).toBeNull();
    });
  });

  describe('Constructor and Basic Properties', () => {
    it('should create an instance with container', () => {
      const workflowEditor = createWorkflowEditor();

      expect(workflowEditor).toBeTruthy();
      expect(workflowEditor.injector).toBe(injector);
    });

    it('should initialize with undefined id by default', () => {
      const workflowEditor = createWorkflowEditor();

      expect(workflowEditor.id).toBeUndefined();
    });

    it('should initialize with undefined name by default', () => {
      const workflowEditor = createWorkflowEditor();

      expect(workflowEditor.name).toBeUndefined();
    });

    it('should initialize with undefined project by default', () => {
      const workflowEditor = createWorkflowEditor();

      expect(workflowEditor.project).toBeUndefined();
    });
  });

  describe('Project Management', () => {
    it('should export empty project schema', () => {
      const workflowEditor = createWorkflowEditor();

      workflowEditor.id = 'project-1';
      workflowEditor.name = 'Test Project';
      workflowEditor.revision = 'v1.0';

      const exported = workflowEditor.exportProject();

      expect(exported).toBeDefined();
      expect(exported.id).toBe('project-1');
      expect(exported.name).toBe('Test Project');
      expect(exported.revision).toBe('v1.0');
      expect(Array.isArray(exported.schema.nodes)).toBe(true);
      expect(Array.isArray(exported.schema.connections)).toBe(true);
    });

    it('should include dataConnectors array in export', () => {
      const workflowEditor = createWorkflowEditor();

      const exported = workflowEditor.exportProject();

      expect(Array.isArray(exported.dataConnectors)).toBe(true);
    });

    it('should call exportProject and store result on saveProject', () => {
      const workflowEditor = createWorkflowEditor();

      spyOn(workflowEditor, 'exportProject').and.returnValue({
        id: 'test-id',
        name: 'Test Project',
        revision: 'v1',
        schema: { nodes: [], connections: [], revision: null },
        dataConnectors: []
      });

      workflowEditor.saveProject();

      expect(workflowEditor.exportProject).toHaveBeenCalled();
      expect(workflowEditor.project).toBeDefined();
      expect(workflowEditor.project?.id).toBe('test-id');
    });

    it('should call WorkflowService.executeNodeJson without nodeId', () => {
      const workflowEditor = createWorkflowEditor();

      const mockProject: Project = {
        id: 'test-id',
        name: 'Test',
        revision: 'v1',
        schema: { nodes: [], connections: [], revision: null },
        dataConnectors: []
      };

      mockWorkflowService.executeNodeJson.and.returnValue(of(mockProject));
      spyOn(workflowEditor, 'exportProject').and.returnValue(mockProject);

      workflowEditor.executeNodeJson();

      expect(mockWorkflowService.executeNodeJson).toHaveBeenCalledWith(mockProject, undefined);
    });

    it('should call WorkflowService.executeNodeJson with nodeId', () => {
      const workflowEditor = createWorkflowEditor();

      const mockProject: Project = {
        id: 'test-id',
        name: 'Test',
        revision: 'v1',
        schema: { nodes: [], connections: [], revision: null },
        dataConnectors: []
      };

      mockWorkflowService.executeNodeJson.and.returnValue(of(mockProject));
      spyOn(workflowEditor, 'exportProject').and.returnValue(mockProject);

      workflowEditor.executeNodeJson('node-123');

      expect(mockWorkflowService.executeNodeJson).toHaveBeenCalledWith(mockProject, 'node-123');
    });

    it('should call updateProjectStatus with response', () => {
      const workflowEditor = createWorkflowEditor();

      const mockProject: Project = {
        id: 'test-id',
        name: 'Test',
        revision: 'v1',
        schema: { nodes: [], connections: [], revision: null },
        dataConnectors: []
      };

      mockWorkflowService.executeNodeJson.and.returnValue(of(mockProject));
      spyOn(workflowEditor, 'exportProject').and.returnValue(mockProject);
      spyOn(workflowEditor, 'updateProjectStatus');

      workflowEditor.executeNodeJson();

      expect(workflowEditor.updateProjectStatus).toHaveBeenCalledWith(mockProject);
    });

    it('should handle empty project updateProjectStatus gracefully', () => {
      const workflowEditor = createWorkflowEditor();

      const emptyProject: Project = {
        id: 'test-id',
        name: 'Test',
        revision: 'v1',
        schema: { nodes: [], connections: [], revision: null },
        dataConnectors: []
      };

      expect(() => workflowEditor.updateProjectStatus(emptyProject)).not.toThrow();
    });
  });

  describe('buildContextMenu', () => {
    it('should build context menu items from registered blocks', () => {
      const container = document.createElement('div');
      const workflowEditor = new WorkflowEditor(container, injector);

      const items = workflowEditor['buildContextMenu']();
      expect(items).toBeDefined();
      expect(Array.isArray(items)).toBe(true);
    });

    it('should group nodes by type', () => {
      const container = document.createElement('div');
      const workflowEditor = new WorkflowEditor(container, injector);

      const items = workflowEditor['buildContextMenu']();
      expect(items.length).toBeGreaterThan(0);
    });
  });

  // Additional coverage for methods that don't require full rendering
  describe('Additional Method Coverage', () => {
    it('should handle exportProject with complex project state', () => {
      const workflowEditor = createWorkflowEditor();

      workflowEditor.id = 'complex-project';
      workflowEditor.name = 'Complex Test Project';
      workflowEditor.revision = 'v2.5';

      const exported = workflowEditor.exportProject();

      expect(exported.id).toBe('complex-project');
      expect(exported.name).toBe('Complex Test Project');
      expect(exported.revision).toBe('v2.5');
      expect(exported.schema).toBeDefined();
      expect(exported.dataConnectors).toBeDefined();
    });

    it('should maintain project reference after saveProject', () => {
      const workflowEditor = createWorkflowEditor();

      workflowEditor.id = 'save-test';
      workflowEditor.name = 'Save Test';

      workflowEditor.saveProject();

      expect(workflowEditor.project).not.toBeNull();
      expect(workflowEditor.project?.id).toBe('save-test');
    });

    it('should handle multiple socket types in socketFactory', () => {
      const workflowEditor = createWorkflowEditor();

      const types = ['SimpleFieldSocket', 'LrsObjectSocket', 'DeepObjectSocket', 'FlatObjectSocket', 'AllSocket'];

      types.forEach(type => {
        const socket = workflowEditor['socketFactory'](type);
        expect(socket).toBeDefined();
        expect(socket.name).toBe(type);
      });
    });

    it('should serialize multiple ports correctly', () => {
      const workflowEditor = createWorkflowEditor();

      const socket1 = new ClassicPreset.Socket('Socket1');
      const socket2 = new ClassicPreset.Socket('Socket2');

      const input = new ClassicPreset.Input(socket1, 'Input Port');
      input.id = 'in-1';

      const output = new ClassicPreset.Output(socket2, 'Output Port');
      output.id = 'out-1';

      const serializedInput = workflowEditor['serializePort'](input);
      const serializedOutput = workflowEditor['serializePort'](output);

      expect(serializedInput.socket.name).toBe('Socket1');
      expect(serializedOutput.socket.name).toBe('Socket2');
    });

    it('should have nodeEditor property after construction', () => {
      const container = document.createElement('div');
      const workflowEditor = new WorkflowEditor(container, injector);

      expect(workflowEditor.nodeEditor).toBeDefined();
    });

    it('should have area property after construction', () => {
      const container = document.createElement('div');
      const workflowEditor = new WorkflowEditor(container, injector);

      expect(workflowEditor.area).toBeDefined();
    });

    it('should have connection property after construction', () => {
      const container = document.createElement('div');
      const workflowEditor = new WorkflowEditor(container, injector);

      expect(workflowEditor.connection).toBeDefined();
    });
  });
});
