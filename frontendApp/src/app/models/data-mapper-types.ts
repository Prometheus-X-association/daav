import { KeyValue } from '@angular/common';
import { Pipe, PipeTransform } from '@angular/core';
import {
  NodeData,
  NodeDataFile,
  NodeDataMysql,
  NodeDataPandasDf,
  NodeDataParquet
} from './node-data';

export type DataType =
  | 'string'
  | 'number'
  | 'date'
  | 'email'
  | 'phone'
  | 'url'
  | 'id'
  | 'currency'
  | 'percentage'
  | 'boolean';

export interface Column {
  id: string;
  name: string;
  type: DataType;
  sample: any[];
  datasetId: string;
}

export interface DatasetMapper {
  id: string;
  name: string;
  columns: Column[];
}

export interface ColumnMapping {
  id: string;
  sources: Column[];
  targetName: string;
}

@Pipe({
    name: 'hasDatasets',
    pure: true,
    standalone: false
})
export class HasDatasetsPipe implements PipeTransform {
  transform(datasets: DatasetMapper[]): boolean {
    return datasets?.length > 0;
  }
}

export class DataMapperUtils {
  /**
   * Transform a NodeData into a dataset useable by MapperComponent
   * @param nodeData the nodeData produce by the parent node
   * @param sourceKey The input key of the current Node who is linked to the parent
   * @returns A DatasetMapper object
   */
  static nodeDataToMapper(
    nodeData: NodeData<any>,
    sourceKey: string
  ): DatasetMapper {
    if (nodeData) {
      if (nodeData.type === 'mysql') {
        let node = nodeData as NodeDataMysql;
        return {
          id: sourceKey,
          name: node.name,
          columns: node.nodeSchema.map((column) => {
            const sample = (node.dataExample as Array<Object>).map(
              (row) => row[column.Field]
            );
            return {
              id: column.Field,
              name: column.Field,
              type: DataMapperUtils.detectTypeFieldMysql(
                column.Type,
                sample[0],
                column.Field
              ),
              sample: sample,
              datasetId: sourceKey,
            };
          }),
        };
      } else if (nodeData.type === 'pandasdf') {
        let node = nodeData as NodeDataPandasDf;
        console.log('nodeDataPandasDf', nodeData);
        return {
          id: sourceKey,
          name: node.name,
          columns: node.nodeSchema.map((column) => {
            const sample = node.dataExample[column.name];
            return {
              id: column.name,
              name: column.name,
              type: DataMapperUtils.detectTypeFieldPandas(
                column.dtype,
                sample[0],
                column.name
              ),
              sample: sample,
              datasetId: sourceKey,
            };
          }),
        };
      } else if (nodeData.type === 'file') {
        let node = nodeData as NodeDataFile;
        console.log('nodeDataFile', nodeData);
        if (
          Array.isArray(nodeData.dataExample) &&
          nodeData.dataExample.length > 0
        ) {
          return {
            id: sourceKey,
            name: node.name,
            columns: Object.keys(nodeData.dataExample[0]).map((columns) => {
              nodeData.dataExample[0][columns];
              return {
                id: columns,
                name: columns,
                type: DataMapperUtils.detectTypeFieldFromValueType(
                  nodeData.dataExample[0][columns],
                  columns
                ),
                sample: [nodeData.dataExample[0][columns]],
                datasetId: sourceKey,
              };
            }),
          };
        } else {
          throw new Error('Empty or malformed NodeDataFile');
        }
      } else if (nodeData.type === 'parquet'){
        console.log('nodeDataParquet', nodeData);
        let node = nodeData as NodeDataParquet;
        let temp = {
          id: sourceKey,
          name: node.name,
          columns: node.nodeSchema.fields.map((column) => {
            const sample = node.dataExample[column.name];
            return {
              id: column.name,
              name: column.name,
              type: DataMapperUtils.detectTypeFieldPandas(
                column.physical_type,
                sample[0],
                column.name
              ),
              sample: sample,
              datasetId: sourceKey,
            };
          }),
        };
        return temp;
      }else {
        throw new Error('Unsupported nodeData type');
      }
    } else {
      throw new Error('nodeData is null or undefined');
    }
  }

  static detectTypeFieldMysql(
    type: string,
    value: string,
    fieldName: string
  ): DataType {
    if (/(_id|Id|id)$/i.test(fieldName)) {
      return 'id';
    }
    if (
      type.includes('int') ||
      type.includes('decimal') ||
      type.includes('float') ||
      type.includes('double')
    ) {
      if (fieldName === 'price' || fieldName === 'cost') {
        return 'currency';
      } else {
        return 'number';
      }
    } else if (
      type.includes('varchar') ||
      type.includes('text') ||
      type.includes('char') ||
      type.includes('blob')
    ) {
      if (value) {
        if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          return 'email';
        } else if (/^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$/.test(value)) {
          return 'url';
        } else if (fieldName.includes('phone') || fieldName.includes('tel')) {
          return 'phone';
        } else if (
          fieldName.includes('percentage') ||
          fieldName.includes('percent') ||
          value.includes('%')
        ) {
          return 'percentage';
        } else {
          return 'string';
        }
      } else {
        return 'string';
      }
    } else if (
      type.includes('date') ||
      type.includes('timestamp') ||
      type.includes('datetime')
    ) {
      return 'date';
    } else if (type.includes('boolean') || type.includes('tinyint(1)')) {
      return 'boolean';
    } else {
      return 'string';
    }
  }

  static detectTypeFieldPandas(
    type: string,
    value: string,
    fieldName: string
  ): DataType {
    if (/(_id|Id|id)$/i.test(fieldName)) {
      return 'id';
    }
    if (type === 'int' || type === 'float') {
      if (fieldName === 'price' || fieldName === 'cost') {
        return 'currency';
      } else {
        return 'number';
      }
    } else if (type === 'object') {
      if (value) {
        if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          return 'email';
        } else if (/^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$/.test(value)) {
          return 'url';
        } else if (fieldName.includes('phone') || fieldName.includes('tel')) {
          return 'phone';
        } else if (
          fieldName.includes('percentage') ||
          fieldName.includes('percent') ||
          (typeof value === 'string') && value?.includes('%')
        ) {
          return 'percentage';
        } else {
          return 'string';
        }
      } else {
        return 'string';
      }
    } else if (type === 'datetime64[ns]') {
      return 'date';
    } else if (type === 'bool') {
      return 'boolean';
    } else {
      return 'string';
    }
  }

  static detectTypeFieldFromValueType(
    value: any,
    fieldName: string
  ): DataType {
    if (/(_id|Id|id)$/i.test(fieldName)) {
      return 'id';
    }

    const valueType = typeof value;

    if (valueType === 'number') {
      if (fieldName === 'price' || fieldName === 'cost') {
        return 'currency';
      }
      return 'number';
    } else if (valueType === 'string') {
      if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        return 'email';
      } else if (/^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$/.test(value)) {
        return 'url';
      } else if (fieldName.includes('phone') || fieldName.includes('tel')) {
        return 'phone';
      } else if (
        fieldName.includes('percentage') ||
        fieldName.includes('percent') ||
        value.includes('%')
      ) {
        return 'percentage';
      }
      return 'string';
    } else if (valueType === 'boolean') {
      return 'boolean';
    } else if (value instanceof Date) {
      return 'date';
    }

    return 'string';
  }
}



