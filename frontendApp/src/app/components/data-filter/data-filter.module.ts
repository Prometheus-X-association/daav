// src/app/data-mapper/data-mapper.module.ts

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataFilterComponent } from './data-filter.component';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { QueryBuilderModule } from 'ngx-query-builder';

@NgModule({
  declarations: [
    DataFilterComponent
  ],
  imports: [
    CommonModule, FormsModule, QueryBuilderModule, IonicModule
  ],
  exports: [
    DataFilterComponent, QueryBuilderModule
  ]
})
export class DataFilterModule { }
