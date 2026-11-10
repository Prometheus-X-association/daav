import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { TestComposantPageRoutingModule } from './test-composant-routing.module';

import { TestComposantPage } from './test-composant.page';
import { DataMapperModule } from 'src/app/components/data-mapper/data-mapper.module';

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        IonicModule,
        TestComposantPageRoutingModule,
        DataMapperModule,
        TestComposantPage
    ]
})
export class TestComposantPageModule {}
