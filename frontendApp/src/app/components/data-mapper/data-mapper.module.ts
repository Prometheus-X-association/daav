// src/app/data-mapper/data-mapper.module.ts

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { DataMapperComponent } from './data-mapper.component';

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        DragDropModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatInputModule,
        MatFormFieldModule,
        DataMapperComponent
    ],
    exports: [
        DataMapperComponent
    ]
})
export class DataMapperModule { }
