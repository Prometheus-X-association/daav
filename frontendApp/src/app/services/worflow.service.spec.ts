import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { WorkflowService } from './worflow.service';
import { Project } from '../models/interfaces/project';

describe('WorkflowService', () => {
  let service: WorkflowService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule]
    });
    service = TestBed.inject(WorkflowService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch workflows and update signal', () => {
    const workflows: Project[] = [{ id: '1', name: 'w1', revision: 'r1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any];

    service.getWorkflows().subscribe((result) => {
      expect(result).toEqual(workflows);
      expect(service.workflows()).toEqual(workflows);
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/`);
    expect(req.request.method).toBe('GET');
    req.flush(workflows);
  });

  it('should get workflow by id', () => {
    const workflow = { id: '1', name: 'w1', revision: 'r1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any;

    service.getWorkflow('1').subscribe((result) => {
      expect(result).toEqual(workflow);
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/1`);
    expect(req.request.method).toBe('GET');
    req.flush(workflow);
  });

  it('should create workflow', () => {
    const workflow = { id: '1', name: 'w1', revision: 'r1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any;

    service.createWorkflow(workflow).subscribe((result) => {
      expect(result).toEqual(workflow);
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/`);
    expect(req.request.method).toBe('POST');
    req.flush(workflow);
  });

  it('should update workflow', () => {
    const workflow = { id: '1', name: 'w1', revision: 'r1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any;

    service.updateWorkflow(workflow).subscribe((result) => {
      expect(result).toEqual(workflow);
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/`);
    expect(req.request.method).toBe('PUT');
    req.flush(workflow);
  });

  it('should delete workflow', () => {
    service.deleteWorkflow('1').subscribe((result) => {
      expect(result).toBeNull();
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });

  it('should execute workflow by id', () => {
    const workflow = { id: '1', name: 'w1', revision: 'r1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any;

    service.executeWorkflow('1').subscribe((result) => {
      expect(result).toEqual(workflow);
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/execute/1`);
    expect(req.request.method).toBe('POST');
    req.flush(workflow);
  });

  it('should execute workflow from JSON', () => {
    const workflow = { id: '1', name: 'w1', revision: 'r1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any;

    service.executeWorkflowJson(workflow).subscribe((result) => {
      expect(result).toEqual(workflow);
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/execute`);
    expect(req.request.method).toBe('POST');
    req.flush(workflow);
  });

  it('should execute node by workflow and node id', () => {
    const workflow = { id: '1', name: 'w1', revision: 'r1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any;

    service.executeNode('w1', 'n1').subscribe((result) => {
      expect(result).toEqual(workflow);
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/execute_node/w1/n1`);
    expect(req.request.method).toBe('POST');
    req.flush(workflow);
  });

  it('should execute node from workflow JSON', () => {
    const workflow = { id: '1', name: 'w1', revision: 'r1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any;

    service.executeNodeJson(workflow, 'n1').subscribe((result) => {
      expect(result).toEqual(workflow);
    });

    const req = httpMock.expectOne(`${service['apiUrl']}/execute_node/n1`);
    expect(req.request.method).toBe('POST');
    req.flush(workflow);
  });

  it('should clear workflows signal', () => {
    service.clearWorkflows();
    expect(service.workflows()).toEqual([]);
  });
});
