import { ChangeDetectorRef, Component, ViewChild, ViewEncapsulation } from '@angular/core';
import { Dataset } from 'src/app/models/dataset';
import { DatasetService } from '../services/dataset.service';
import { LoadingService } from '../services/loading.service';
import { DatasetsModalComponent } from '../components/datasets-modal/datasets-modal.component';
import { TransformationModalComponent } from '../components/transformation-modal/transformation-modal.component';
import { WorkflowPage } from '../pages/worflow/workflow.page';
import { Project } from '../models/interfaces/project';

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
    standalone: false
})

export class MainPage {
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

  constructor( private cd: ChangeDetectorRef, public datasetService : DatasetService, public loadingService: LoadingService) {
  }

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
