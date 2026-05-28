import { DatasetApi } from "./dataset-api";
import { DatasetElasticSearch } from "./dataset-elastic-search";
import { DatasetFile } from "./dataset-file";
import { DatasetMongo } from "./dataset-mongo";
import { DatasetMySQL } from "./dataset-my-sql";
import { MysqlSchema } from "./dataset-schema";
import { DatasetsI } from "./datasets-i";

export interface Pagination {
  page: number;
  perPage: number;
  nextUrl?: string;
}

export interface DatasetContentParams {
  database: string;
  table: string;
}

export interface DatasetContentRequest {
  dataset: DatasetsI;
  pagination: Pagination;
  datasetParams: DatasetContentParams;
}

export interface MySQLContentResponse extends DatasetContentResponse{
  databases?: string[];
  tables?: string[];
  table_description?: MysqlSchema;
}

export interface MongoContentResponse extends DatasetContentResponse {
  databases?: string[];
  collections?: string[];
}

export interface ElasticSearchContentResponse extends DatasetContentResponse {
  indices?: string[];
}

export interface FileContentResponse extends DatasetContentResponse {

}

export interface ApiContentResponse extends DatasetContentResponse  {
  next_url?: string;
  prev_url?: string;
}
export interface DatasetContentResponse {
  data?: Array<any>;
  total_rows?: number;
  limit?: number;
  current_page?: number;
}

export type DatasetResponseMap<T> =
  T extends DatasetMySQL ? MySQLContentResponse :
  T extends DatasetMongo ? MongoContentResponse :
  T extends DatasetElasticSearch ? ElasticSearchContentResponse :
  T extends DatasetFile ? FileContentResponse :
  T extends DatasetApi ? ApiContentResponse :
  DatasetContentResponse;

// --- Type guards ---

export function isMySQLContentResponse(res: unknown): res is MySQLContentResponse {
  return !!res && typeof res === 'object' && (
    Array.isArray((res as MySQLContentResponse).databases) ||
    Array.isArray((res as MySQLContentResponse).tables)
  );
}

export function isMongoContentResponse(res: unknown): res is MongoContentResponse {
  return !!res && typeof res === 'object' && Array.isArray((res as MongoContentResponse).collections);
}

export function isElasticSearchContentResponse(res: unknown): res is ElasticSearchContentResponse {
  return !!res && typeof res === 'object' && Array.isArray((res as ElasticSearchContentResponse).indices);
}

export function isApiContentResponse(res: unknown): res is ApiContentResponse {
  return !!res && typeof res === 'object' && (
    'next_url' in (res as ApiContentResponse) ||
    'prev_url' in (res as ApiContentResponse)
  );
}
