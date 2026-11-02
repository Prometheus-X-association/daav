import { $localize } from '@angular/localize/init';
import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonicModule } from '@ionic/angular';
import { NgxJsonViewerModule } from 'ngx-json-viewer';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { DatasetElasticSearch } from 'src/app/models/dataset-elastic-search';
import {
  ElasticClusterInfo,
  ElasticIndex,
  ElasticQueryResponse,
  ElasticService,
} from 'src/app/services/elastic.service';

const QUERY_PAGE_SIZE = 20;

@Component({
  selector: 'app-elastic-dashboard',
  templateUrl: './elastic-dashboard.component.html',
  styleUrls: ['./elastic-dashboard.component.scss'],
  imports: [CommonModule, FormsModule, IonicModule, NgxJsonViewerModule],
})
export class ElasticDashboardComponent extends DashboardComponent implements OnInit {
  @Input() override dataset: DatasetElasticSearch;

  private elasticService = inject(ElasticService);

  info: ElasticClusterInfo;
  infoError: string;
  indices: ElasticIndex[] = [];
  indicesError: string;
  loadingIndices = false;
  includeHidden = false;
  indexFilter = '';

  selectedIndex: ElasticIndex;
  mapping: Record<string, any>;
  mappingError: string;

  queryText = '';
  queryPage = 1;
  queryResult: ElasticQueryResponse;
  queryError: string;
  queryRunning = false;
  readonly queryPageSize = QUERY_PAGE_SIZE;

  newIndexName = '';
  newIndexMappings = '';
  createError: string;
  createMessage: string;
  creating = false;

  constructor() {
    super();
  }

  ngOnInit() {
    this.loadInfo();
    this.loadIndices();
  }

  private errorMessage(err: any): string {
    const detail = err?.error?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg ?? JSON.stringify(d)).join(', ');
    }
    return err?.message ?? $localize`Unknown error`;
  }

  loadInfo() {
    this.infoError = null;
    this.elasticService.getInfo(this.dataset.id).subscribe({
      next: (info) => (this.info = info),
      error: (err) => (this.infoError = this.errorMessage(err)),
    });
  }

  loadIndices() {
    this.loadingIndices = true;
    this.indicesError = null;
    this.elasticService.getIndices(this.dataset.id, this.includeHidden).subscribe({
      next: (indices) => {
        this.indices = indices;
        this.loadingIndices = false;
        const fixed = this.dataset.index && indices.find((i) => i.index === this.dataset.index);
        if (!this.selectedIndex && fixed) {
          this.selectIndex(fixed);
        }
      },
      error: (err) => {
        this.indicesError = this.errorMessage(err);
        this.loadingIndices = false;
      },
    });
  }

  get filteredIndices(): ElasticIndex[] {
    const filter = this.indexFilter.trim().toLowerCase();
    return filter
      ? this.indices.filter(
          (i) => i.index.includes(filter) || i.aliases.some((a) => a.includes(filter))
        )
      : this.indices;
  }

  get totalDocs(): number {
    return this.indices.reduce((sum, i) => sum + (i.docsCount ?? 0), 0);
  }

  selectIndex(index: ElasticIndex) {
    this.selectedIndex = index;
    this.mapping = null;
    this.mappingError = null;
    this.queryResult = null;
    this.queryError = null;
    this.queryPage = 1;
    this.elasticService.getMapping(this.dataset.id, index.index).subscribe({
      next: (mapping) => (this.mapping = mapping),
      error: (err) => (this.mappingError = this.errorMessage(err)),
    });
    this.runQuery();
  }

  runQuery(page = 1) {
    if (!this.selectedIndex) {
      return;
    }
    this.queryPage = page;
    this.queryRunning = true;
    this.queryError = null;
    this.elasticService
      .query(this.dataset.id, {
        index: this.selectedIndex.index,
        query: this.queryText.trim() || null,
        page,
        size: QUERY_PAGE_SIZE,
      })
      .subscribe({
        next: (result) => {
          this.queryResult = result;
          this.queryRunning = false;
        },
        error: (err) => {
          this.queryError = this.errorMessage(err);
          this.queryResult = null;
          this.queryRunning = false;
        },
      });
  }

  get queryPageCount(): number {
    return this.queryResult ? Math.max(1, Math.ceil(this.queryResult.total / QUERY_PAGE_SIZE)) : 1;
  }

  get queryColumns(): string[] {
    const columns = new Set<string>();
    this.queryResult?.data.forEach((row) => Object.keys(row).forEach((key) => columns.add(key)));
    return [...columns];
  }

  displayValue(value: any): string {
    if (value === null || value === undefined) {
      return '';
    }
    return typeof value === 'object' ? JSON.stringify(value) : String(value);
  }

  createIndex() {
    this.createError = null;
    this.createMessage = null;
    const name = this.newIndexName.trim();
    let mappings: object = null;
    if (this.newIndexMappings.trim()) {
      try {
        mappings = JSON.parse(this.newIndexMappings);
      } catch (e) {
        this.createError = $localize`The mappings are not valid JSON: ${(e as Error).message}`;
        return;
      }
    }
    this.creating = true;
    this.elasticService.createIndex(this.dataset.id, name, mappings).subscribe({
      next: () => {
        this.creating = false;
        this.createMessage = $localize`Index ${name} created`;
        this.newIndexName = '';
        this.newIndexMappings = '';
        this.loadIndices();
      },
      error: (err) => {
        this.creating = false;
        this.createError = this.errorMessage(err);
      },
    });
  }

  /** Deletion is not available from DAAV: give the command to run instead (without secrets) */
  get deleteCommand(): string {
    if (!this.selectedIndex) {
      return '';
    }
    const url = `${(this.dataset.url ?? '').replace(/\/+$/, '')}/${this.selectedIndex.index}`;
    const auth = {
      basic: ` -u ${this.dataset.user || '<user>'}`,
      apiKey: ' -H "Authorization: ApiKey <api-key>"',
      bearer: ' -H "Authorization: Bearer <token>"',
    }[this.dataset.authMode ?? (this.dataset.user ? 'basic' : 'none')] ?? '';
    return `curl -X DELETE${auth} "${url}"`;
  }

  copy(text: string) {
    navigator.clipboard?.writeText(text);
  }

  formatSize(bytes: number): string {
    if (bytes === null || bytes === undefined) {
      return '-';
    }
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    let size = bytes;
    while (size >= 1024 && i < units.length - 1) {
      size /= 1024;
      i++;
    }
    return `${Math.round(size * 10) / 10} ${units[i]}`;
  }
}
