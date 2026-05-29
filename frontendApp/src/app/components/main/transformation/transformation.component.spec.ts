import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TransformationComponent } from './transformation.component';
import { LoadingService } from 'src/app/services/loading.service';
import { WorkflowService } from 'src/app/services/worflow.service';
import { DatasetService } from 'src/app/services/dataset.service';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { of } from 'rxjs';
import { MatDialog } from '@angular/material/dialog';
import { StatusNode } from 'src/app/enums/status-node';

describe('TransformationComponent', () => {
  let component: TransformationComponent;
  let fixture: ComponentFixture<TransformationComponent>;
  let workflowSpy: jasmine.SpyObj<WorkflowService>;
  let datasetSpy: jasmine.SpyObj<DatasetService>;
  let dialogSpy: jasmine.SpyObj<MatDialog>;

  beforeEach(waitForAsync(() => {
    workflowSpy = jasmine.createSpyObj('WorkflowService', ['getWorkflows', 'deleteWorkflow', 'executeWorkflowJson'], {
      workflows: () => []
    } as any);
    workflowSpy.getWorkflows.and.returnValue(of([]));
    workflowSpy.deleteWorkflow.and.returnValue(of(null));
    workflowSpy.executeWorkflowJson.and.returnValue(of({
      id: 'project-1',
      name: 'Project 1',
      revision: 'v1',
      schema: { nodes: [], connections: [], revision: null },
      dataConnectors: []
    } as any));

    datasetSpy = jasmine.createSpyObj('DatasetService', ['get']);
    dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);
    dialogSpy.open.and.returnValue({ afterClosed: () => of(true) } as any);

    const loadingSpy = jasmine.createSpyObj('LoadingService', ['present', 'dismiss']);

    TestBed.configureTestingModule({
      declarations: [TransformationComponent],
      imports: [IonicModule.forRoot()],
      providers: [
        { provide: LoadingService, useValue: loadingSpy },
        { provide: WorkflowService, useValue: workflowSpy },
        { provide: DatasetService, useValue: datasetSpy },
        { provide: MatDialog, useValue: dialogSpy },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(TransformationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should emit transformationView when changeView is called', () => {
    spyOn(component.transformationView, 'emit');

    component.changeView();

    expect(component.transformationView.emit).toHaveBeenCalledWith('rete');
  });

  it('should emit createWorkflow when createNewWorkflow is called', () => {
    spyOn(component.createWorkflow, 'emit');

    component.createNewWorkflow();

    expect(component.createWorkflow.emit).toHaveBeenCalled();
  });

  it('should emit loadWorkflow when loadSelectedWorkflow is called', () => {
    spyOn(component.loadWorkflow, 'emit');
    const project = { id: 'p1', name: 'P1', revision: 'v1', schema: { nodes: [], connections: [], revision: null }, dataConnectors: [] } as any;

    component.loadSelectedWorkflow(project);

    expect(component.loadWorkflow.emit).toHaveBeenCalledWith(project);
  });

  it('should copy text to clipboard and prevent default', async () => {
    const writeSpy = spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.resolve());
    const event = {
      preventDefault: jasmine.createSpy('preventDefault'),
      stopPropagation: jasmine.createSpy('stopPropagation')
    } as any;

    await component.copyToClipboard('text', event);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(event.stopPropagation).toHaveBeenCalled();
    expect(writeSpy).toHaveBeenCalledWith('text');
  });

  it('should delete workflow when dialog confirms', () => {
    const projectId = 'delete-1';
    component.deleteWorkflow(projectId);

    expect(dialogSpy.open).toHaveBeenCalled();
    expect(workflowSpy.deleteWorkflow).toHaveBeenCalledWith(projectId);
    expect(workflowSpy.getWorkflows).toHaveBeenCalled();
  });

  it('should set workflow status to error when execution returns non-valid nodes', () => {
    const project = {
      id: 'p1',
      name: 'Project 1',
      revision: 'v1',
      schema: {
        nodes: [{ data: { status: StatusNode.Error } }],
        connections: [],
        revision: null
      },
      dataConnectors: []
    } as any;

    workflowSpy.executeWorkflowJson.and.returnValue(of(project));
    spyOn(component.loadWorkflow, 'emit');

    component.executeWorkflow(project);

    expect(datasetSpy.get).toHaveBeenCalled();
    expect(component.loadWorkflow.emit).toHaveBeenCalledWith(project);
    expect(component.workflowsStatus.get('p1')).toBe('error');
  });
});
