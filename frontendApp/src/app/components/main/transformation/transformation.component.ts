import { Component, OnInit, Output, EventEmitter, inject, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { WorkflowService } from 'src/app/services/worflow.service';
import { Project } from 'src/app/models/interfaces/project';
import { LoadingService } from 'src/app/services/loading.service';
import {MatDialog} from '@angular/material/dialog';
import { ConfirmDeletionModalComponent } from 'src/app/components/confirm-deletion-modal/confirm-deletion-modal.component';
import { WorkflowUpdateRulesModalComponent } from 'src/app/components/workflow-update-rules-modal/workflow-update-rules-modal.component';
import { StatusNode } from 'src/app/enums/status-node';
import { DatasetService } from 'src/app/services/dataset.service';

@Component({
    selector: 'app-transformation',
    templateUrl: './transformation.component.html',
    styleUrls: ['../datasets/datasets.component.scss', './transformation.component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush,
    standalone: false
})
export class TransformationComponent  implements OnInit {
  @Output() transformationView = new EventEmitter<string>();
  @Output() createWorkflow = new EventEmitter<string>();
  @Output() loadWorkflow = new EventEmitter<Project>();
  readonly dialog = inject(MatDialog);
  workflowsStatus = new Map<string, string>();

  constructor(public workflowService: WorkflowService, public loadingService: LoadingService, public cd: ChangeDetectorRef, private datasetService: DatasetService) { }

  ngOnInit() {
    this.workflowService.getWorkflows().subscribe();
  }

  changeView() {
    this.transformationView.emit('rete')
  }

  deleteWorkflow(id: string){
    const dialogRef = this.dialog.open(ConfirmDeletionModalComponent, {
      data: { message: 'Do you really want to delete this workflow ?' }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result === true) {
        this.workflowService.deleteWorkflow(id).subscribe(() =>
          this.workflowService.getWorkflows().subscribe()
        );
      }
    })
  }

  updateRules(id: string){
    const dialogRef = this.dialog.open(WorkflowUpdateRulesModalComponent)
    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        console.log('Automatic:', result.automatic);
        console.log('Update Text:', result.updateText);

        // treatment
      }
    });
  }

  createNewWorkflow() {
    this.createWorkflow.emit();
  }

  loadSelectedWorkflow(project: Project) {
    this.loadWorkflow.emit(project);

  }

  executeWorkflow(project: Project) {
    this.workflowsStatus.set(project.id, 'running');
    this.workflowService.executeWorkflowJson(project).subscribe((projectResult) => {
      // Mise à jour du projet avec les résultats
      project.schema.nodes = projectResult.schema.nodes;
      
      projectResult.schema.nodes.forEach(node => {
        if (node.data?.selectDataSource?.value) {
          // Conserver le label "Dataset"
          node.data.selectDataSource = {
            ...node.data.selectDataSource,
            label: "Dataset",
          };
          // Nettoyer fileName si présent
          if (node.data.fileName) {
            node.data.fileName = { value: null, label: null };
          }
        }
      });

      // Rafraîchir la liste des datasets
      this.datasetService.get();
      
      // Mettre à jour l'éditeur via l'événement
      this.loadWorkflow.emit(projectResult);

      // Mise à jour du statut global
      if (project.schema.nodes.every(node => node.data.status === StatusNode.Valid)) {
        this.workflowsStatus.delete(project.id);
      } else {
        this.workflowsStatus.set(project.id, 'error');
      }
      
      this.cd.detectChanges();
    });
  }

  copyToClipboard(text: string, event :Event) {
  event.preventDefault(); // Empêche le clic de déclencher le bouton parent
  event.stopPropagation(); // Empêche le clic de déclencher le bouton parent
  navigator.clipboard.writeText(text).then(() => {
  }).catch(err => {
  });
}

}

