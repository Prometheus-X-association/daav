import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { BaseService } from './base.service.service';

export interface MysqlDatabase {
  name: string;
  charset: string;
  collation: string;
  tables: number;
  /** Sum of the InnoDB estimates: approximate */
  approxRows: number;
  sizeBytes: number;
}

export interface MysqlServerInfo {
  version: string;
  versionComment: string;
  currentUser: string;
  charset: string;
  collation: string;
  timeZone: string;
  host: string;
  uptimeSeconds: number | null;
  threadsConnected: number | null;
  databases: MysqlDatabase[];
}

export interface MysqlTable {
  name: string;
  type: 'table' | 'view';
  engine: string | null;
  /** InnoDB estimate: approximate */
  approxRows: number | null;
  sizeBytes: number | null;
  collation: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  comment: string;
  columns: number;
}

export interface MysqlColumn {
  name: string;
  type: string;
  nullable: boolean;
  key: string;
  default: string | null;
  extra: string;
  comment: string;
}

/**
 * Read-only MySQL information on a MySQL dataset (server, databases, tables and columns).
 */
@Injectable({
  providedIn: 'root',
})
export class MysqlService extends BaseService {
  private readonly http = inject(HttpClient);

  private url(datasetId: string, path: string): string {
    return `${this.urlBack}/datasets/${encodeURIComponent(datasetId)}/mysql/${path}`;
  }

  getInfo(datasetId: string): Observable<MysqlServerInfo> {
    return this.http.get<MysqlServerInfo>(this.url(datasetId, 'info'));
  }

  getTables(datasetId: string, database: string): Observable<MysqlTable[]> {
    return this.http.get<MysqlTable[]>(this.url(datasetId, `databases/${encodeURIComponent(database)}/tables`));
  }

  getColumns(datasetId: string, database: string, table: string): Observable<MysqlColumn[]> {
    return this.http.get<MysqlColumn[]>(
      this.url(datasetId, `databases/${encodeURIComponent(database)}/tables/${encodeURIComponent(table)}/columns`)
    );
  }
}
