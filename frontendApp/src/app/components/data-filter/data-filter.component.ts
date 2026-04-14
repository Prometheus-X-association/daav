import { Component, Input, OnInit, SimpleChanges } from '@angular/core';
import { FieldMap, QueryBuilderConfig } from 'ngx-query-builder';
import { DatasetMapper, DataType } from 'src/app/models/data-mapper-types';
import { DataFilterControl } from '../widgets/data-filter-widget/data-filter-widget.component';


@Component({
    selector: 'app-data-filter',
    templateUrl: './data-filter.component.html',
    styleUrls: ['./data-filter.component.scss'],
    standalone: false
})
export class DataFilterComponent implements OnInit{

  @Input() datasets: DatasetMapper[] = [];
  @Input() filterControl: DataFilterControl;

  config: QueryBuilderConfig = {
    fields: {},
  }

  get query(){
    return this.filterControl.query;
  }

  set query(value){
    this. filterControl.query = value;
  }

  constructor() { }

  ngOnInit(): void {
    this.buildQueryConfig()

    if(!this.query.condition){
      this.query.condition = 'and'
    }
  }

  private buildQueryConfig(): void{
    this.config.fields = {};

    if(this.datasets && this.datasets.length > 0){
      const { columns } = this.datasets[0];
      const fieldMap: FieldMap = {};
          
      if (columns) {
        columns.forEach(column => {
          fieldMap[column.id] = {
            name: column.name,
            type: this.mapDataTypeToFieldType(column.type),
          };
        });
        this.config = {
          fields: fieldMap,
        };
      }
    }
    
    
  }

  private mapDataTypeToFieldType(dataType: DataType): 'string'| 'number' | 'time' | 'date' | 'category' | 'boolean' {
    switch (dataType) {
      case 'string':
      case 'email':
      case 'phone':
      case 'url':
      case 'id':
        return 'string';
      case 'number':
      case 'currency':
      case 'percentage':
        return 'number';
      case 'date':
        return 'date';
      case 'boolean':
        return 'boolean';
      default:
        return 'string';
    }
  }
}
