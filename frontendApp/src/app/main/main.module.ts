import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MainPage } from './main.page';

import { Tab1PageRoutingModule } from './main-routing.module';
import { ComponentsModule } from '../components-module';
import { MatTableModule } from '@angular/material/table';
import { RenderComponent } from '../components/main/render/render.component';
import { DatasetsComponent } from '../components/main/datasets/datasets.component';
import { TransformationComponent } from '../components/main/transformation/transformation.component';
import { MatPaginatorModule } from '@angular/material/paginator';
import {MatTabsModule} from '@angular/material/tabs';
import { LoadingComponent } from '../components/main/loading/loading.component';
import { DatasetsModalComponent } from '../components/datasets-modal/datasets-modal.component';
import { TransformationModalComponent } from '../components/transformation-modal/transformation-modal.component';
import { NgxJsonViewerModule } from 'ngx-json-viewer';
import { WorkflowPageModule } from '../pages/worflow/workflow.module';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    Tab1PageRoutingModule,
    ComponentsModule,
    MatTableModule,
    MatPaginatorModule,
    MatTabsModule,
    ReactiveFormsModule,
    NgxJsonViewerModule,
    WorkflowPageModule
  ],
  declarations: [MainPage,RenderComponent,DatasetsComponent,TransformationComponent,DatasetsModalComponent, TransformationModalComponent]
})
export class MainPageModule {}
