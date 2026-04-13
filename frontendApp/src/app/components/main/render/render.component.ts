import { DatasetService } from 'src/app/services/dataset.service';
import { Component, Input, ViewChild, OnInit,  OnChanges, SimpleChanges, output, ElementRef, reflectComponentType, ViewContainerRef, ChangeDetectorRef, Renderer2 } from '@angular/core';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { LoadingService } from 'src/app/services/loading.service';
import { DataRenderTypes } from 'src/app/models/data-render-types';
import { Dataset } from 'src/app/models/dataset'
import { NgxJsonViewerModule } from 'ngx-json-viewer';
import { MatTab } from '@angular/material/tabs';
import { isApiContentResponse, isElasticSearchContentResponse, isMongoContentResponse, isMySQLContentResponse } from 'src/app/models/dataset-content-response';

@Component({
    selector: 'app-render',
    templateUrl: './render.component.html',
    styleUrls: ['./render.component.scss'],
    standalone: false
})

export class RenderComponent implements OnInit, OnChanges {
  @ViewChild(MatPaginator) paginator: MatPaginator;
  @ViewChild("dashboardContainer") dashboardContainer: ElementRef;
  @ViewChild("dashboardContainerAnchor", {read: ViewContainerRef}) dashboardContainerAnchor: ViewContainerRef;
  datasetsLoaded = output<boolean>();

  // Définition des options de taille de page
  pageSizeOptions = [5, 10, 25, 50, 100];

  dataDefault: DataRenderTypes = {
    dbNames: null,
    tableNames: null,
    displayedColumns: null,
    fiche: {
      items: null,
      limit: null,
      total: null,
      current_page: null,
    },
    selectedDataset: null,
    renderTabIndex: 0,
    pagination: {
      perPage: 100, // Valeur par défaut
      page: 1
    },
    datasetParams: {
      database: "",
      table: ""
    }
  }

  data : DataRenderTypes;
  selectedDatasetId: string | null;

  @Input() dataset: Dataset;
  filterTables = "";

  constructor(public datasetService : DatasetService, public loadingService : LoadingService, private cd : ChangeDetectorRef, private render: Renderer2) {
    this.data = this.dataDefault;
  }


  isObject(val): boolean {
    if (typeof val === 'object' && val !== null) {
      return true;
    }else{
      return false;
    }
  }

  ngOnInit() {
    console.log("render initialized");
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['dataset']) {
      this.data = this.dataDefault;
      this.getDatasetContent(this.dataset, "", "", 0);
    }
  }

  async getDatasetContent(dataset: Dataset | null, db: any, table: any, tabIndex: number) {
    try {
      this.loadingService.loadingOn();
      if (this.data.fiche.total && this.paginator) {
        this.paginator.pageIndex = 0;
        this.paginator.pageSize = this.data.pagination.perPage;
      }
      this.data.datasetParams.database = db;
      this.data.datasetParams.table = table;
      this.data.pagination.page = 1;
      await this.getContent(dataset)
      this.datasetsLoaded.emit(true);
      this.data.renderTabIndex = tabIndex;
      this.loadingService.loadingOff();

      this.cd.detectChanges();

      // debugger;
      // create dashboard based on dataset type
      // console.log(this.dashboardContainer.nativeElement);
      for(const e of this.dashboardContainer.nativeElement.children){
        if(e.id != "dashboard-container-anchor"){
          e.remove();
        }
      };

      const dashboardComponent = this.dashboardContainerAnchor.createComponent(this.dataset.dashboardComponent);
      // this.render.appendChild(this.dashboardContainer.nativeElement, dashboardComponent.location.nativeElement);
      dashboardComponent.setInput("dataset", this.data.selectedDataset);

    }
    catch(err) {
      this.loadingService.loadingOff();
      console.error("err while loading datasets", err)
    }
  }

  async pageChange($event: PageEvent) {
    this.loadingService.loadingOn();
    this.data.pagination.page = $event.pageIndex + 1;
    this.data.pagination.perPage = $event.pageSize; // Ajout de cette lignex
    if(this.data.fiche.nextUrl || this.data.fiche.prevUrl){
      if ($event.pageIndex > $event.previousPageIndex) {
        this.data.pagination.nextUrl = this.data.fiche.nextUrl;
      } else {
        this.data.pagination.nextUrl = this.data.fiche.prevUrl;
      }
    } else {
      this.data.pagination.nextUrl = null;
    }
    try {
      await this.getContent();
      this.loadingService.loadingOff();
    }
    catch {
      this.loadingService.loadingOff();
    }
  }

  selectedDataset($event:any){
    let table_name = document.querySelectorAll('.table-name');
    table_name.forEach(t_n => {
      t_n.classList.remove('active-dataset')
    });
    $event.target.classList.toggle('active-dataset');
  }


  getContent(dataset?: Dataset | null):Promise<void> {
    return new Promise((resolve,reject) => {
      const {database, table} = this.data.datasetParams;
      this.selectedDatasetId = this.data.selectedDataset !== null ? this.data.selectedDataset.id : null;
      if(dataset){
        this.data.selectedDataset = dataset;
      }

      this.datasetService.getContentDataset(this.data.selectedDataset,this.data.pagination, {database, table}).subscribe((res) => {
        this.data.pagination.nextUrl = null;
        if (res) {
          if (res.data) {
            this.data.fiche = {
              items: res.data,
              limit: res.limit,
              total: res.total_rows,
              current_page: res.current_page
            }
          }

          if (this.selectedDatasetId !== this.data.selectedDataset.id) {
            if (!res.data) {
              this.data.displayedColumns = [];
              this.data.fiche = {
                items: null,
                limit: null,
                total: null,
                current_page: null,
              };
              this.data.renderTabIndex = 0;
            }
            if (isMySQLContentResponse(res) || isMongoContentResponse(res)) {
              this.data.dbNames = res.databases;
            }
            else{
              this.data.dbNames = null;
            }

            if (isMongoContentResponse(res)) {
              this.data.tableNames = res.collections;
            }
            else if (isMySQLContentResponse(res)) {
              this.data.tableNames = res.tables;
            }
            else if (isElasticSearchContentResponse(res)) {
              this.data.tableNames = res.indices;
            }
            else{
              this.data.tableNames = null;
            }

          }
          if(isApiContentResponse(res)){
            this.data.fiche.nextUrl = res.next_url;
            this.data.fiche.prevUrl = res.prev_url;
            this.data.pagination.perPage  = res.limit ? res.limit : this.data.pagination.perPage;
          }

          if (this.data.dbNames !== null || this.data.tableNames !== null) {
            // When db and/or table are not specified
            let items = this.data.fiche.items;
            let keys: string[];
            items.length !== 0 ? keys = Object.keys(items[0]) : keys = [" "]
            this.data.displayedColumns = keys;
          }
          else if (this.data.fiche.items?.length > 0){
            // For a single table
            this.data.displayedColumns = Object.keys(this.data.fiche.items[0]);
          }

          resolve();
        }
        // Connection work but the user don't have access to this dataset
        else{
          this.data.displayedColumns = [];
          this.data.fiche = {
            items: null,
            limit: null,
            total: null,
            current_page: null,
          };
          this.data.renderTabIndex = 0;
          alert("Connection successful but unable to get data.")
          reject();
        }
      },error => {
        // Connection don't work
        console.log("error",error)
        this.data.displayedColumns = [];
        this.data.fiche = {
          items: null,
          limit: null,
          total: null,
          current_page: null,
        };
        this.data.renderTabIndex = 0;
        alert("Connection error.")
        this.data.pagination.nextUrl = null;
        reject();
      });
    })
  }
  applyFilter(event: Event) {
    const filterValue = (event.target as HTMLInputElement).value;
    this.filterTables = filterValue.trim().toLowerCase();
  }

  String(s: string | string[]){
    return String(s);
  }
}
