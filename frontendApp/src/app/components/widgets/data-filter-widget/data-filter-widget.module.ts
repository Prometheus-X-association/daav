import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataFilterModule } from '../../data-filter/data-filter.module';
import { QueryBuilderModule } from 'ngx-query-builder';
import { IonicModule } from '@ionic/angular';



@NgModule({
  declarations: [],
  imports: [
    CommonModule, DataFilterModule, QueryBuilderModule, IonicModule
  ],
})
export class DataFilterWidgetModule { }
