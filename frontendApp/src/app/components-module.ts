import { NgModule } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { DataMapperModule } from './components/data-mapper/data-mapper.module';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { SelectWidgetComponent } from './components/widgets/select-widget/select-widget.component';
import { CommonModule } from '@angular/common';
import { NodeLoaderWidgetComponent } from './components/widgets/node-loader-widget/node-loader-widget.component';
import { IonicModule } from '@ionic/angular';
import { HasDatasetsPipe } from './models/data-mapper-types';
import { DataMapperWidgetComponent } from './components/widgets/data-mapper-widget/data-mapper-widget.component';
import { ButtonWidgetComponent } from './components/widgets/button-widget/button-widget.component';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { InputAutoCompleteWidgetComponent } from './components/widgets/auto-complete-widget/input-auto-complete-widget.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { CheckboxWidgetComponent } from './components/widgets/checkbox-widget/checkbox-widget.component';
import { DataFilterWidgetComponent } from './components/widgets/data-filter-widget/data-filter-widget.component';
import { QueryBuilderModule } from 'ngx-query-builder';
import { JsonInputsWidgetComponent } from './components/widgets/json-inputs-widget/json-inputs-widget.component';
import { TextDisplayWidgetComponent } from './components/widgets/text-display-widget/text-display-widget.component';
import { JsonEditorComponent, JsonEditorOptions } from 'ang-jsoneditor';
import { CdkAccordionModule } from '@angular/cdk/accordion';
import { DashboardsModule } from './components/dashboards/dashboards.module';
import { UserProfileComponent } from './components/user-profile/user-profile.component';
import { DataFilterComponent } from './components/data-filter/data-filter.component';
import { DataFilterModule } from './components/data-filter/data-filter.module';

@NgModule({
  declarations: [
    TextDisplayWidgetComponent,
    CheckboxWidgetComponent,
    InputAutoCompleteWidgetComponent,
    ButtonWidgetComponent,
    SelectWidgetComponent,
    NodeLoaderWidgetComponent,
    DataMapperWidgetComponent,
    HasDatasetsPipe,
    DataFilterWidgetComponent,
    JsonInputsWidgetComponent,
    UserProfileComponent,
  ],
  exports: [
    TextDisplayWidgetComponent,
    CheckboxWidgetComponent,
    InputAutoCompleteWidgetComponent,
    ButtonWidgetComponent,
    SelectWidgetComponent,
    NodeLoaderWidgetComponent,
    DataMapperWidgetComponent,
    HasDatasetsPipe,
    DataFilterWidgetComponent,
    JsonInputsWidgetComponent,
    UserProfileComponent,
  ],
  imports: [
    FormsModule,
    IonicModule,
    ReactiveFormsModule,
    MatAutocompleteModule,
    MatTableModule,
    DataMapperModule,
    DataFilterModule,
    MatSelectModule,
    MatFormFieldModule,
    CommonModule,
    MatIconModule,
    MatButtonModule,
    MatInputModule,
    MatCheckboxModule,
    QueryBuilderModule,
    JsonEditorComponent,
    CdkAccordionModule,
  ],
})
export class ComponentsModule {}
