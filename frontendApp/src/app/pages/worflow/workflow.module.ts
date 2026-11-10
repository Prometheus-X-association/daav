import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkflowPageRoutingModule } from './wokflow-routing.module';
import { WorkflowPage } from './workflow.page';

@NgModule({
    imports: [
        IonicModule,
        CommonModule,
        FormsModule,
        WorkflowPageRoutingModule,
        WorkflowPage
    ],
    exports: [WorkflowPage]
})
export class WorkflowPageModule {}
