import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { TabsPageRoutingModule } from './tabs-routing.module';

import { TabsPage } from './tabs.page';
import { ComponentsModule } from '../components-module';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import { LoadingComponent } from '../components/main/loading/loading.component';
@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    MatProgressSpinnerModule,
    FormsModule,
    TabsPageRoutingModule,
    LoadingComponent
  ],
  declarations: [TabsPage],
})
export class TabsPageModule {}
