import { ChangeDetectorRef, Component, ViewChild, ViewEncapsulation, inject } from '@angular/core';
import { Dataset } from 'src/app/models/dataset';
import { DatasetService } from '../services/dataset.service';
import { LoadingService } from '../services/loading.service';
import { DatasetsModalComponent } from '../components/datasets-modal/datasets-modal.component';
import { TransformationModalComponent } from '../components/transformation-modal/transformation-modal.component';
import { WorkflowPage } from '../pages/worflow/workflow.page';
import { Project } from '../models/interfaces/project';
import { IonicModule } from '@ionic/angular';
import { AppToolbarComponent } from '../components/app-toolbar/app-toolbar.component';
import { RouterLink } from '@angular/router';
import { DatasetsComponent } from '../components/main/datasets/datasets.component';
import { TransformationComponent } from '../components/main/transformation/transformation.component';
import { MatTabGroup, MatTab, MatTabContent } from '@angular/material/tabs';
import { RenderComponent } from '../components/main/render/render.component';

enum Tabs {
  datasets,
  rendu,
  transformation
}
@Component({
    selector: 'app-main',
    templateUrl: 'main.page.html',
    styleUrls: ['main.page.scss'],
    encapsulation: ViewEncapsulation.None,
    imports: [IonicModule, AppToolbarComponent, RouterLink, DatasetsModalComponent, TransformationModalComponent, DatasetsComponent, TransformationComponent, MatTabGroup, MatTab, RenderComponent, MatTabContent, WorkflowPage]
})

export class MainPage {
  private readonly cd = inject(ChangeDetectorRef);
  datasetService = inject(DatasetService);
  loadingService = inject(LoadingService);

  fileName = '';
  dataset: Dataset;
  activeTab = Tabs.datasets;
  datasetSelected: any;
  transformationView: string = "list";
  loadProjectId: string;
  sidePanelCollapsed = false;

  get Tabs(){
    return Tabs;
  }

  width = {
    left: "small",
    right: "large"
  }

  pagination = {
    perPage: 100,
    page: 1
  }

  getDataset(dataset: Dataset) {
    this.dataset = dataset;
  }

  onSelectionChange() {
    this.cd.detectChanges();
  }

  @ViewChild("datasetModal", { static: false }) datasetModal: DatasetsModalComponent;
  @ViewChild("transformationModal", { static: false }) transformationModal: TransformationModalComponent;
  @ViewChild(WorkflowPage) workflowEditor: WorkflowPage;
  displayedColumns: string[] = [];
  datasets: any;
  dataSource: any[] = [];
  matTabIndex = 0;

  loadDataset(){
    this.matTabIndex = 1;
  }

  openDatasetsModal(){
    this.datasetModal.modal.isOpen = true;
    this.datasetModal.formDatabase.reset();
  }

  changeTransformationView(view: string){
    this.transformationView = view;
  }

  get isWorkflowOpen(): boolean {
    return this.matTabIndex === Tabs.transformation && this.transformationView === 'rete';
  }

  // The side panel can only be collapsed while a workflow is open in the editor
  get isSidePanelCollapsed(): boolean {
    return this.sidePanelCollapsed && this.isWorkflowOpen;
  }

  toggleSidePanel() {
    this.sidePanelCollapsed = !this.sidePanelCollapsed;
  }

  closeWorkflow() {
    this.loadProjectId = undefined;
    this.sidePanelCollapsed = false;
    this.transformationView = 'list';
  }

  ionViewWillEnter() {
  }

  closeModalAddConnection() {
    this.datasetModal.modal.isOpen = false;
  }

  createWorkflow() {
    if (this.workflowEditor) {
      this.workflowEditor.newProject();
    }
    else{
      // The editor is created afterwards: make sure it does not reopen the last loaded workflow
      this.loadProjectId = undefined;
    }
  }

  loadWorkflow(project: Project) {
    if (this.workflowEditor) {
      this.workflowEditor.loadProject(project);
    }
    else{
      this.loadProjectId = project.id;
    }
  }
}
