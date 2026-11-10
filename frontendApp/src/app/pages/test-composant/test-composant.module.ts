import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { TestComposantPageRoutingModule } from './test-composant-routing.module';

import { TestComposantPage } from './test-composant.page';


@NgModule({
    imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    TestComposantPageRoutingModule,
    TestComposantPage
]
})
export class TestComposantPageModule {}
