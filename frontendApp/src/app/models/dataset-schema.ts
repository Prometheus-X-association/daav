/**
 * Represents a dataset schema: MysqlSchema, PandasSchema or ParquetSchema.
 */
export type DatasetSchema = MysqlSchema | PandasSchema | ParquetSchema

/**
 * Represents a MySQL schema as an array of field definitions.
 */
export interface MysqlSchema extends Array<{
  /**
   * The name of the field.
   */
  Field: string;
  /**
   * The data type of the field.
   */
  Type: string;
  /**
   * Indicates whether the field can be null.
   */
  Null: string;
  /**
   * Indicates if the field is a key.
   */
  Key: string;
  /**
   * The default value of the field.
   */
  Default: any;
  /**
   * Any extra information about the field.
   */
  Extra: string;
}> {}

/**
 * Represents a column definition in a Pandas DataFrame.
 */
interface PandasColumn {
  /**
   * The name of the column.
   */
  name: string;
  /**
   * The data type of the column (e.g., 'int64', 'float64', 'object', 'datetime64[ns]', etc.).
   */
  dtype: string;
  /**
   * Indicates whether the column can contain null values.
   */
  nullable: boolean;
  /**
   * Number of non-null values in the column.
   */
  count?: number;
  /**
   * Inner columns for nested structures (optional).
   */
  nested?: PandasColumn[];
}

/**
 * Represents a Pandas DataFrame schema as an array of column definitions.
 */
export interface PandasSchema extends Array<PandasColumn> {}

export class PandasSchemaUtils {

  /**
   * Checks if the given schema is a deep object schema.
   * A deep object schema is defined as having at least one column with nested columns.
   * @param schema The PandasSchema to check.
   * @returns True if the schema is a deep object schema, false otherwise.
   */
  static isDeepObjectSchema(schema: PandasSchema): boolean {
    return schema.some((column) => {
      return column.nested && column.nested.length > 0;
    });
  }
}

/**
 * Represents a column definition in a Parquet file.
 */
interface ParquetColumn {
  /**
   * The name of the column.
   */
  name: string;

  /**
   * The physical type of the column in Parquet format.
   */
  physical_type: string;

  /**
   * The logical type of the column (optional).
   */
  logical_type: string | null;
}



/**
 * Represents a Parquet file schema structure.
 */
export interface ParquetSchema {
   /**
   * Array of column definitions.
   */
  fields: ParquetColumn[];
}
