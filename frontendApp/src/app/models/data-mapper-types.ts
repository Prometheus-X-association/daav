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
    pure: true
})
export class HasDatasetsPipe implements PipeTransform {
  transform(datasets: DatasetMapper[]): boolean {
    return datasets?.length > 0;
  }
}

const ID_FIELD_PATTERN = /(_id|Id|id)$/i;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const URL_PATTERN = /^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$/;
const MYSQL_NUMBER_TYPES = ['int', 'decimal', 'float', 'double'];
const MYSQL_TEXT_TYPES = ['varchar', 'text', 'char', 'blob'];
const MYSQL_DATE_TYPES = ['date', 'timestamp', 'datetime'];
const PANDAS_SIMPLE_TYPES = new Map<string, DataType>([
  ['datetime64[ns]', 'date'],
  ['bool', 'boolean'],
]);

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
    if (ID_FIELD_PATTERN.test(fieldName)) {
      return 'id';
    }
    if (MYSQL_NUMBER_TYPES.some((mysqlType) => type.includes(mysqlType))) {
      return DataMapperUtils.numberOrCurrency(fieldName);
    }
    if (MYSQL_TEXT_TYPES.some((mysqlType) => type.includes(mysqlType))) {
      return value ? DataMapperUtils.detectStringSubtype(value, fieldName) : 'string';
    }
    if (MYSQL_DATE_TYPES.some((mysqlType) => type.includes(mysqlType))) {
      return 'date';
    }
    if (type.includes('boolean') || type.includes('tinyint(1)')) {
      return 'boolean';
    }
    return 'string';
  }

  static detectTypeFieldPandas(
    type: string,
    value: string,
    fieldName: string
  ): DataType {
    if (ID_FIELD_PATTERN.test(fieldName)) {
      return 'id';
    }
    if (type === 'int' || type === 'float') {
      return DataMapperUtils.numberOrCurrency(fieldName);
    }
    if (type === 'object') {
      // The sample of an object column is not always a string
      return value
        ? DataMapperUtils.detectStringSubtype(value, fieldName, (sample) => typeof sample === 'string' && sample.includes('%'))
        : 'string';
    }
    return PANDAS_SIMPLE_TYPES.get(type) ?? 'string';
  }

  static detectTypeFieldFromValueType(
    value: any,
    fieldName: string
  ): DataType {
    if (ID_FIELD_PATTERN.test(fieldName)) {
      return 'id';
    }

    const valueType = typeof value;

    if (valueType === 'number') {
      return DataMapperUtils.numberOrCurrency(fieldName);
    } else if (valueType === 'string') {
      return DataMapperUtils.detectStringSubtype(value, fieldName);
    } else if (valueType === 'boolean') {
      return 'boolean';
    } else if (value instanceof Date) {
      return 'date';
    }

    return 'string';
  }

  private static numberOrCurrency(fieldName: string): DataType {
    return fieldName === 'price' || fieldName === 'cost' ? 'currency' : 'number';
  }

  /**
   * Detect the subtype of a text value: email, URL, phone, percentage or plain string.
   * The percent sign check is only called when the other checks do not match.
   */
  private static detectStringSubtype(
    value: any,
    fieldName: string,
    hasPercentSign: (value: any) => boolean = (sample) => sample.includes('%')
  ): DataType {
    if (EMAIL_PATTERN.test(value)) {
      return 'email';
    }
    if (URL_PATTERN.test(value)) {
      return 'url';
    }
    if (fieldName.includes('phone') || fieldName.includes('tel')) {
      return 'phone';
    }
    if (fieldName.includes('percentage') || fieldName.includes('percent') || hasPercentSign(value)) {
      return 'percentage';
    }
    return 'string';
  }
}



