import { WorkflowService } from '../../services/worflow.service';
import { Component, ElementRef, Injector, ViewChild, AfterViewInit, OnInit, input, Input, Output, EventEmitter, OnChanges, SimpleChanges, AfterContentInit, AfterViewChecked, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { WorkflowEditor } from '../../core/workflow-editor';
import { environment } from 'src/environments/environment';
import { Project } from '../../models/interfaces/project';
import { AppUtils } from '../../models/app-utils';
import { ActivatedRoute } from '@angular/router';
import { $localize } from '@angular/localize/init';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDeletionModalComponent } from '../../components/confirm-deletion-modal/confirm-deletion-modal.component';

@Component({
    selector: 'app-workflow',
    templateUrl: 'workflow.page.html',
    styleUrls: ['workflow.page.scss'],
    standalone: false
})
export class WorkflowPage implements AfterViewInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly dialog = inject(MatDialog);
  workflow: WorkflowEditor;
  exported: Project;
  toolbar: HTMLElement;
  @Input() projectId: string;
  @Output() closed = new EventEmitter<void>();

  constructor(private injector: Injector,private route: ActivatedRoute,public workflowService : WorkflowService) {
    this.route.queryParams
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(params => {
        this.projectId = params['projectId'];
      });
  }
  @ViewChild("rete", {static: false}) container!: ElementRef;

  ngAfterViewInit(): void {
    setTimeout(() => {
      const el = this.container.nativeElement;

      if (el) {
        this.workflow = new WorkflowEditor(el, this.injector);
        this.workflow.name = this.getDefaultName();
        this.workflow.markAsSaved();
      }
      if (!environment.production) {
        (window as any).workflow = this.workflow;
      }
      if (this.projectId) {
        this.loadProject(this.projectId);
      }
    }, 0);
  }


  /**
   *Load a Project in the workflow
   * @param project : Project | string (id of a project)
   */
  public loadProject(project : Project | string){
    if (this.workflow && project){
      if ( typeof project === 'string'){
        project = this.workflowService.workflows().find(w => w.id == project);
      }
      if (project){
        this.workflow.importProject(project);
      }
    }
  }


  /**
   *Reset the workflow for a new Project
   * @param project
   */
  public newProject(){
      if (this.workflow ){
        this.workflow.resetWorkflow(this.getDefaultName());
      }
    }

  protected export(){
    this.exported = this.workflow.exportProject();

    console.log(this.exported);
    console.log(JSON.stringify(this.exported));
  }

  protected import(){
    this.workflow.importProject(this.exported);
  }


   public saveProject(){
    const project = this.workflow.exportProject();
    if (project.id){
      this.workflowService.updateWorkflow(project).subscribe({next : data =>{
        console.log(data);
        this.workflow.markAsSaved(project);
        this.workflowService.getWorkflows().subscribe({
          next: (data) => {
            console.log(data);
          }
        });
      },error: (error)=>{
        alert("Error updating project");
        console.log(error);
      }});
    } else {
      this.workflowService.createWorkflow(project).subscribe({
        next: (data) => {
          this.workflow.id = data.id;
          this.workflow.markAsSaved({ ...project, id: data.id });
          this.workflowService.getWorkflows().subscribe({
            next: (data) => {
              console.log(data);
            }
          });
        },
        error: (error) => {
          alert("Error creating project");
          console.log(error);
        }
      });
    }
  }

  /**
   * Close the workflow, asking for confirmation when it has unsaved changes
   */
  public closeProject(){
    if (!this.workflow?.hasUnsavedChanges()){
      this.closed.emit();
      return;
    }
    const dialogRef = this.dialog.open(ConfirmDeletionModalComponent, {
      data: { message: $localize `:@@closeUnsavedWorkflow:This workflow has unsaved changes. Close it anyway?` }
    });
    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.closed.emit();
      }
    });
  }

  private getDefaultName(){
    const projectDefaultName = $localize `:@@newWorkflow:New Workflow`;
    if (this.workflowService.workflows().length > 0){
      let nameExists = this.workflowService.workflows().some(w => w.name === projectDefaultName);
      let counter = 1;
      let newName = projectDefaultName;

      while (nameExists) {
        newName = `${projectDefaultName} (${counter})`;
        nameExists = this.workflowService.workflows().some(w => w.name === newName);
        counter++;
      }
      return newName;

    } else {
      return projectDefaultName;
    }
  }

}
