import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseService } from './base.service.service';
import { NodeDataPandasDf } from '../models/node-data';

export interface ElasticClusterInfo {
  clusterName: string;
  version: string;
  status: 'green' | 'yellow' | 'red' | null;
  numberOfNodes: number | null;
  activeShards: number | null;
  unassignedShards: number | null;
}

export interface ElasticIndex {
  index: string;
  health: 'green' | 'yellow' | 'red' | null;
  status: string;
  docsCount: number | null;
  sizeBytes: number | null;
  primaries: number | null;
  replicas: number | null;
  aliases: string[];
}

export interface ElasticQueryRequest {
  index: string;
  /** Query DSL clause (JSON) or Lucene query string; empty matches all documents */
  query?: string | object;
  fields?: string[];
  page?: number;
  size?: number;
  includeId?: boolean;
}

export interface ElasticQueryResponse {
  total: number;
  data: Record<string, any>[];
}

/**
 * Elasticsearch-specific operations on an Elasticsearch dataset
 * (cluster information, indices, mappings and queries).
 */
@Injectable({
  providedIn: 'root',
})
export class ElasticService extends BaseService {
  constructor(private http: HttpClient) {
    super();
  }

  private url(datasetId: string, path: string): string {
    return `${this.urlBack}/datasets/${encodeURIComponent(datasetId)}/elastic/${path}`;
  }

  getInfo(datasetId: string): Observable<ElasticClusterInfo> {
    return this.http.get<ElasticClusterInfo>(this.url(datasetId, 'info'));
  }

  getIndices(datasetId: string, includeHidden = false): Observable<ElasticIndex[]> {
    return this.http.get<ElasticIndex[]>(this.url(datasetId, 'indices'), {
      params: { includeHidden },
    });
  }

  getMapping(datasetId: string, index: string): Observable<Record<string, any>> {
    return this.http.get<Record<string, any>>(
      this.url(datasetId, `indices/${encodeURIComponent(index)}/mapping`)
    );
  }

  createIndex(datasetId: string, index: string, mappings?: object): Observable<{ index: string; created: boolean }> {
    return this.http.post<{ index: string; created: boolean }>(this.url(datasetId, 'indices'), {
      index,
      mappings: mappings ?? null,
    });
  }

  query(datasetId: string, request: ElasticQueryRequest): Observable<ElasticQueryResponse> {
    return this.http.post<ElasticQueryResponse>(this.url(datasetId, 'query'), request);
  }

  sample(datasetId: string, request: ElasticQueryRequest): Observable<NodeDataPandasDf> {
    return this.http.post<NodeDataPandasDf>(this.url(datasetId, 'sample'), request);
  }
}
