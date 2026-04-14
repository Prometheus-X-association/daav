// src/app/data-mapper/data-mapper.module.ts

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataFilterComponent } from './data-filter.component';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';

@NgModule({
  declarations: [
    DataFilterComponent
  ],
  imports: [
    CommonModule, FormsModule, IonicModule
  ],
  exports: [
    DataFilterComponent
  ]
})
export class DataFilterModule { }
