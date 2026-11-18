import { WorkflowNodeEditor } from './workflow-node-editor';
import { Injector } from "@angular/core";
import { WorkflowEditor } from './workflow-editor';

describe('WorkflowNodeEditor', () => {
  let injector: Injector;
  let workflowEditor: WorkflowEditor;

  beforeEach(() => {
    injector = jasmine.createSpyObj('Injector', ['get']);
    workflowEditor = jasmine.createSpyObj('WorkflowEditor', ['emit']);
  });

  it('should create an instance', () => {
    const editor = new WorkflowNodeEditor(injector, workflowEditor);
    expect(editor).toBeTruthy();
  });

  it('should have an injector', () => {
    const editor = new WorkflowNodeEditor(injector, workflowEditor);
    expect(editor.injector).toBe(injector);
  });

  it('should have a core', () => {
    const editor = new WorkflowNodeEditor(injector, workflowEditor);
    expect(editor.core).toBe(workflowEditor);
  });
});
