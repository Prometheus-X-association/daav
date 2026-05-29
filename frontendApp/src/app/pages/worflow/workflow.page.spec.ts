import '@angular/localize/init';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { FormsModule } from '@angular/forms';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { WorkflowPage } from './workflow.page';
import { WorkflowService } from '../../services/worflow.service';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('WorkflowPage', () => {
  let component: WorkflowPage;
  let fixture: ComponentFixture<WorkflowPage>;
  let workflowServiceSpy: any;

  beforeEach(async () => {
    const activatedRouteSpy = {
      queryParams: of({ projectId: 'test' })
    };

    workflowServiceSpy = jasmine.createSpyObj('WorkflowService', [
      'workflows',
      'updateWorkflow',
      'createWorkflow',
      'getWorkflows'
    ]);
    workflowServiceSpy.workflows.and.returnValue([]);
    workflowServiceSpy.updateWorkflow.and.returnValue(of({}));
    workflowServiceSpy.createWorkflow.and.returnValue(of({ id: 'new-id' }));
    workflowServiceSpy.getWorkflows.and.returnValue(of([]));

    await TestBed.configureTestingModule({
      declarations: [WorkflowPage],
      imports: [IonicModule.forRoot(), FormsModule],
      providers: [
        { provide: ActivatedRoute, useValue: activatedRouteSpy },
        { provide: WorkflowService, useValue: workflowServiceSpy },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkflowPage);
    component = fixture.componentInstance;
    component.workflow = {
      importProject: jasmine.createSpy('importProject'),
      resetWorkflow: jasmine.createSpy('resetWorkflow'),
      exportProject: jasmine.createSpy('exportProject').and.returnValue({ id: undefined }),
      name: ''
    } as any;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load project by id string', () => {
    const project = { id: 'test', name: 'Test Project' } as any;
    workflowServiceSpy.workflows.and.returnValue([project]);

    component.loadProject('test');

    expect(component.workflow.importProject).toHaveBeenCalledWith(project);
  });

  it('should load project object directly', () => {
    const project = { id: 'direct-id', name: 'Direct Project' } as any;

    component.loadProject(project);

    expect(component.workflow.importProject).toHaveBeenCalledWith(project);
  });

  it('should newProject call resetWorkflow with default name', () => {
    workflowServiceSpy.workflows.and.returnValue([]);

    component.newProject();

    expect(component.workflow.resetWorkflow).toHaveBeenCalledWith('New Workflow');
  });

  it('should return a unique default name when existing workflows contain the default', () => {
    workflowServiceSpy.workflows.and.returnValue([
      { name: 'New Workflow' },
      { name: 'New Workflow (1)' }
    ]);

    const name = (component as any).getDefaultName();

    expect(name).toBe('New Workflow (2)');
  });

  it('should import exported workflow', () => {
    component.exported = { id: 'exp' } as any;

    (component as any).import();

    expect(component.workflow.importProject).toHaveBeenCalledWith(component.exported);
  });

  it('should create project when saveProject has no id', () => {
    component.workflow.exportProject = jasmine.createSpy('exportProject').and.returnValue({ id: undefined } as any);

    component.saveProject();

    expect(workflowServiceSpy.createWorkflow).toHaveBeenCalled();
    expect(component.workflow.id).toBe('new-id');
  });

  it('should update project when saveProject has an id', () => {
    component.workflow.exportProject = jasmine.createSpy('exportProject').and.returnValue({ id: 'exists' } as any);

    component.saveProject();

    expect(workflowServiceSpy.updateWorkflow).toHaveBeenCalled();
  });
});
