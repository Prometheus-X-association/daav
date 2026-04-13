import { ChangeDetectorRef, Component, ViewChild, ViewEncapsulation } from '@angular/core';
import { Dataset } from 'src/app/models/dataset';
import { DatasetService } from '../services/dataset.service';
import { LoadingService } from '../services/loading.service';
import { DatasetsModalComponent } from '../components/datasets-modal/datasets-modal.component';
import { TransformationModalComponent } from '../components/transformation-modal/transformation-modal.component';
import { WorkflowPage } from '../pages/worflow/workflow.page';
import { Project } from '../models/interfaces/project';
import { UserProfileComponent } from '../components/user-profile/user-profile.component';
import { ModalController } from '@ionic/angular';

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
  themes: {
    class: string,
    name: string
  }[] = [
    {
    class: "",
    name: "Thème par défaut"
  },
  {
    class: "theme-ptx",
    name: "Thème PTX"
  }
]

fonts: string[] = ["poppins", "OpenDyslexic"]

  constructor( private cd: ChangeDetectorRef, public datasetService : DatasetService, public loadingService: LoadingService,private modalController: ModalController) {
    this.applyTheme(localStorage.getItem("theme"))
    this.applyFont(localStorage.getItem("font"))
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

  ionViewWillEnter() {
  }

  closeModalAddConnection() {
    this.datasetModal.modal.isOpen = false;
  }

  createWorkflow() {
    if (this.workflowEditor) {
      this.workflowEditor.newProject();
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

  isMenuOpen = false;
  menuIcon = "settings-outline";
  htmlClassList = document.querySelector("html").classList
  body = document.querySelector("body")
  html = document.querySelector("html")

  toggleMenu() {
    this.isMenuOpen = !this.isMenuOpen;
    this.menuIcon = this.isMenuOpen ? "close-outline" : "settings-outline"
  }

  removeAllThemeClasses():void {
    this.themes.forEach((theme) => {
      if (theme.class !== "") {
        this.htmlClassList.remove(theme.class)
      }
    })
  }

  removeAllFontClasses():void {
    this.fonts.forEach((font) => {
      if (font !== "") {
        this.htmlClassList.remove(font)
      }
    })
  }

  applyTheme(value):void {
    this.removeAllThemeClasses()

    if (value && value !== "") {
      this.htmlClassList.add(value)
    }

    localStorage.setItem("theme", value)
  }

  applyFont(value:string):void {
    this.removeAllFontClasses()

    if (value && value !== "") {
      this.htmlClassList.add(value)
    }

    localStorage.setItem("font", value);
  }

    /**
   * Open user profile modal
   */
  async openUserProfile() {
    const modal = await this.modalController.create({
      component: UserProfileComponent
    });
    return await modal.present();
  }
}
