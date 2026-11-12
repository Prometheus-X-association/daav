import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { MysqlDashboardComponent } from './mysql-dashboard.component';
import { MysqlService } from 'src/app/services/mysql.service';
import { DatasetMySQL } from 'src/app/models/dataset-my-sql';

describe('MysqlDashboardComponent', () => {
  let fixture: ComponentFixture<MysqlDashboardComponent>;
  let component: MysqlDashboardComponent;
  let mysql: jasmine.SpyObj<MysqlService>;

  const shop = { name: 'shop', charset: 'utf8mb4', collation: 'c', tables: 2, approxRows: 30, sizeBytes: 32768 };
  const crm = { name: 'crm', charset: 'utf8mb4', collation: 'c', tables: 1, approxRows: 5, sizeBytes: 16384 };
  const info = {
    version: '8.4.0', versionComment: 'MySQL Community Server - GPL', currentUser: 'daav@%',
    charset: 'utf8mb4', collation: 'c', timeZone: 'SYSTEM', host: 'db', uptimeSeconds: 93784,
    threadsConnected: 3, databases: [shop, crm],
  };
  const tables = [
    { name: 'orders', type: 'table', engine: 'InnoDB', approxRows: 20, sizeBytes: 16384, collation: 'c',
      createdAt: '2026-01-02T10:00:00', updatedAt: null, comment: '', columns: 4 },
    { name: 'v_orders', type: 'view', engine: null, approxRows: null, sizeBytes: null, collation: null,
      createdAt: null, updatedAt: null, comment: 'VIEW', columns: 2 },
  ] as any[];

  function create(datasetValues: any = {}) {
    fixture = TestBed.createComponent(MysqlDashboardComponent);
    component = fixture.componentInstance;
    component.dataset = new DatasetMySQL({ id: 'ds1', name: 'db', type: 'mysql', host: 'db', ...datasetValues } as any);
    fixture.detectChanges();
  }

  beforeEach(async () => {
    mysql = jasmine.createSpyObj('MysqlService', ['getInfo', 'getTables', 'getColumns']);
    mysql.getInfo.and.returnValue(of(info as any));
    mysql.getTables.and.returnValue(of(tables));
    mysql.getColumns.and.returnValue(of([{ name: 'id', type: 'int', nullable: false, key: 'PRI', default: null, extra: 'auto_increment', comment: '' }]));

    await TestBed.configureTestingModule({
      imports: [MysqlDashboardComponent],
      providers: [
        { provide: MysqlService, useValue: mysql },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting(),
      ],
    }).compileComponents();
  });

  it('should load the server information and databases', () => {
    create();
    expect(component.totalTables).toBe(3);
    expect(component.totalSize).toBe(49152);
    expect(fixture.nativeElement.querySelectorAll('table.databases tbody tr')).toHaveSize(2);
    // several databases: none is opened automatically
    expect(mysql.getTables).not.toHaveBeenCalled();
  });

  it('should open the only database of the server', () => {
    mysql.getInfo.and.returnValue(of({ ...info, databases: [shop] } as any));
    create();
    expect(mysql.getTables).toHaveBeenCalledWith('ds1', 'shop');
    expect(mysql.getColumns).not.toHaveBeenCalled();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('table.tables')).toBeTruthy();
  });

  it('should show only the table of a single table dataset', () => {
    mysql.getInfo.and.returnValue(of({ ...info, databases: [{ ...shop, tables: 1 }] } as any));
    mysql.getTables.and.returnValue(of([tables[0]]));
    create({ database: 'shop', table: 'orders' });
    fixture.detectChanges();
    expect(component.singleTable).toBeTrue();
    expect(mysql.getColumns).toHaveBeenCalledWith('ds1', 'shop', 'orders');
    const element: HTMLElement = fixture.nativeElement;
    expect(element.querySelector('table.databases')).toBeNull();
    expect(element.querySelector('table.tables')).toBeNull();
    expect(element.querySelectorAll('table.columns tbody tr')).toHaveSize(1);
    expect(element.textContent).toContain('shop.orders');
    expect(element.textContent).toContain('InnoDB');
  });

  it('should tell when the table of a single table dataset is not visible', () => {
    mysql.getInfo.and.returnValue(of({ ...info, databases: [{ ...shop, tables: 0 }] } as any));
    mysql.getTables.and.returnValue(of([]));
    create({ database: 'shop', table: 'orders' });
    fixture.detectChanges();
    expect(component.tableNotFound).toBeTrue();
    expect(fixture.nativeElement.querySelector('[role=alert]').textContent).toContain('does not exist');
  });

  it('should list the tables of a selected database', () => {
    create();
    component.selectDatabase(shop);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelectorAll('table.tables tbody tr')).toHaveSize(2);
    component.tableFilter = 'v_';
    expect(component.filteredTables.map((t) => t.name)).toEqual(['v_orders']);
  });

  it('should show the backend error', () => {
    mysql.getInfo.and.returnValue(throwError(() => ({ error: { detail: 'MySQL refused the credentials' } })));
    create();
    expect(component.infoError).toBe('MySQL refused the credentials');
    expect(fixture.nativeElement.querySelector('[role=alert]').textContent).toContain('credentials');
  });

  it('should format sizes and uptimes', () => {
    create();
    expect(component.formatSize(null)).toBe('-');
    expect(component.formatSize(1536)).toBe('1.5 KB');
    expect(component.formatUptime(93784)).toBe('1d 2h');
    expect(component.formatUptime(3720)).toBe('1h 2min');
    expect(component.formatUptime(59)).toBe('0min');
  });
});
