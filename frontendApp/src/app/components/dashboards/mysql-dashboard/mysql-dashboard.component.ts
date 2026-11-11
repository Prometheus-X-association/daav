import { $localize } from '@angular/localize/init';
import { Component, Input, OnInit, inject } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IonButton, IonSearchbar, IonSkeletonText } from '@ionic/angular/standalone';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { DatasetMySQL } from 'src/app/models/dataset-my-sql';
import { MysqlColumn, MysqlDatabase, MysqlServerInfo, MysqlService, MysqlTable } from 'src/app/services/mysql.service';

@Component({
  selector: 'app-mysql-dashboard',
  templateUrl: './mysql-dashboard.component.html',
  styleUrls: ['./mysql-dashboard.component.scss'],
  imports: [DatePipe, DecimalPipe, FormsModule, IonButton, IonSearchbar, IonSkeletonText],
})
export class MysqlDashboardComponent extends DashboardComponent implements OnInit {
  @Input() override dataset: DatasetMySQL;

  private readonly mysqlService = inject(MysqlService);

  info: MysqlServerInfo;
  infoError: string;

  selectedDatabase: MysqlDatabase;
  tables: MysqlTable[] = [];
  tablesError: string;
  loadingTables = false;
  tableFilter = '';

  selectedTable: MysqlTable;
  columns: MysqlColumn[];
  columnsError: string;

  /** The dataset points to one table: the dashboard shows that table instead of the database lists */
  get singleTable(): boolean {
    return !!(this.dataset.database && this.dataset.table);
  }

  /** Single table dataset whose table is not visible with the dataset credentials */
  get tableNotFound(): boolean {
    return this.singleTable && !!this.info && !this.loadingTables && !this.tablesError && !this.selectedTable;
  }

  ngOnInit() {
    this.loadInfo();
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
    this.mysqlService.getInfo(this.dataset.id).subscribe({
      next: (info) => {
        this.info = info;
        const current = this.selectedDatabase && info.databases.find((d) => d.name === this.selectedDatabase.name);
        const preferred = current ?? (info.databases.length === 1 ? info.databases[0] : null);
        if (preferred) {
          this.selectDatabase(preferred);
        }
      },
      error: (err) => (this.infoError = this.errorMessage(err)),
    });
  }

  get totalTables(): number {
    return this.info?.databases.reduce((sum, d) => sum + d.tables, 0) ?? 0;
  }

  get totalSize(): number {
    return this.info?.databases.reduce((sum, d) => sum + d.sizeBytes, 0) ?? 0;
  }

  selectDatabase(database: MysqlDatabase) {
    const keepTable = this.selectedDatabase?.name === database.name ? this.selectedTable?.name : null;
    this.selectedDatabase = database;
    this.selectedTable = null;
    this.columns = null;
    this.tables = [];
    this.tablesError = null;
    this.loadingTables = true;
    this.mysqlService.getTables(this.dataset.id, database.name).subscribe({
      next: (tables) => {
        this.tables = tables;
        this.loadingTables = false;
        // re-open the table shown before a refresh, or the table the dataset points to
        const name = keepTable ?? (this.dataset.database === database.name ? this.dataset.table : null);
        const table = name && tables.find((t) => t.name === name);
        if (table) {
          this.selectTable(table);
        }
      },
      error: (err) => {
        this.tablesError = this.errorMessage(err);
        this.loadingTables = false;
      },
    });
  }

  get filteredTables(): MysqlTable[] {
    const filter = this.tableFilter.trim().toLowerCase();
    return filter ? this.tables.filter((t) => t.name.toLowerCase().includes(filter)) : this.tables;
  }

  selectTable(table: MysqlTable) {
    this.selectedTable = table;
    this.columns = null;
    this.columnsError = null;
    this.mysqlService.getColumns(this.dataset.id, this.selectedDatabase.name, table.name).subscribe({
      next: (columns) => (this.columns = columns),
      error: (err) => (this.columnsError = this.errorMessage(err)),
    });
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

  formatUptime(seconds: number): string {
    if (seconds === null || seconds === undefined) {
      return '-';
    }
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (days) {
      return $localize`${days}d ${hours}h`;
    }
    return hours ? $localize`${hours}h ${minutes}min` : $localize`${minutes}min`;
  }
}
