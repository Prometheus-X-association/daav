import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { MatTabsModule } from '@angular/material/tabs';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { RenderComponent } from './render.component';
import { LoadingService } from 'src/app/services/loading.service';
import { DatasetService } from 'src/app/services/dataset.service';

describe('RenderComponent', () => {
  let component: RenderComponent;
  let fixture: ComponentFixture<RenderComponent>;
  let loadingServiceSpy: jasmine.SpyObj<LoadingService>;
  let datasetServiceSpy: jasmine.SpyObj<DatasetService>;

  beforeEach(waitForAsync(() => {
    loadingServiceSpy = jasmine.createSpyObj('LoadingService', ['loadingOn', 'loadingOff']);
    datasetServiceSpy = jasmine.createSpyObj('DatasetService', ['getContentDataset']);

    TestBed.configureTestingModule({
    schemas: [NO_ERRORS_SCHEMA],
    imports: [MatTabsModule, BrowserAnimationsModule, RenderComponent],
    providers: [
        provideIonicAngular(),
        { provide: LoadingService, useValue: loadingServiceSpy },
        { provide: DatasetService, useValue: datasetServiceSpy },
        provideHttpClientTesting()
    ]
}).compileComponents();

    fixture = TestBed.createComponent(RenderComponent);
    component = fixture.componentInstance;
    component.dataset = { name: 'Test Dataset', id: 'test-id', type: 'test-type' } as any;
    component.data = {
      dbNames: [],
      tableNames: [],
      displayedColumns: [],
      fiche: { items: [], limit: 10, total: 0, current_page: 1 },
      selectedDataset: { name: 'Test Dataset', id: 'test-id' } as any,
      renderTabIndex: 0,
      pagination: { perPage: 100, page: 1 },
      datasetParams: { database: '', table: '' }
    };
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should identify objects correctly', () => {
    expect(component.isObject({})).toBeTrue();
    expect(component.isObject(null)).toBeFalse();
    expect(component.isObject('string')).toBeFalse();
  });

  it('should convert values to strings', () => {
    expect(component.String('123')).toBe('123');
    expect(component.String(['a', 'b'])).toBe('a,b');
  });

  it('should call getDatasetContent when dataset input changes', async () => {
    spyOn(component, 'getDatasetContent').and.returnValue(Promise.resolve());
    component.ngOnChanges({
      dataset: {
        currentValue: component.dataset,
        previousValue: null,
        firstChange: true,
        isFirstChange: () => true
      } as any
    });

    expect(component.getDatasetContent).toHaveBeenCalled();
  });

  it('should update pagination and call getContent on pageChange', async () => {
    spyOn(component, 'getContent').and.returnValue(Promise.resolve());

    await component.pageChange({ pageIndex: 1, pageSize: 5, previousPageIndex: 0 } as any);

    expect(component.data.pagination.page).toBe(2);
    expect(component.data.pagination.perPage).toBe(5);
    expect(component.getContent).toHaveBeenCalled();
    expect(loadingServiceSpy.loadingOn).toHaveBeenCalled();
    expect(loadingServiceSpy.loadingOff).toHaveBeenCalled();
  });

  it('should resolve getContent when service returns data', async () => {
    datasetServiceSpy.getContentDataset.and.returnValue(of({
      data: [{ col1: 'val' }],
      limit: 2,
      total_rows: 1,
      current_page: 1
    } as any));

    await component.getContent();

    expect(component.data.fiche.items).toEqual([jasmine.objectContaining({ col1: 'val' })] as any);
    expect(component.data.displayedColumns).toEqual(['col1']);
  });

  it('should set dbNames and tableNames for MySQL content when dataset changes', async () => {
    const newDataset = { name: 'New Dataset', id: 'other-id' } as any;
    datasetServiceSpy.getContentDataset.and.returnValue(of({
      data: [{ col1: 'val' }],
      limit: 2,
      total_rows: 1,
      current_page: 1,
      databases: ['db1'],
      tables: ['t1']
    } as any));

    await component.getContent(newDataset);

    expect(component.data.dbNames).toEqual(['db1']);
    expect(component.data.tableNames).toEqual(['t1']);
    expect(component.data.displayedColumns).toEqual(['col1']);
  });

  it('should set api pagination URLs when api response is received', async () => {
    const newDataset = { name: 'New Dataset', id: 'other-id' } as any;
    datasetServiceSpy.getContentDataset.and.returnValue(of({
      data: [{ col1: 'val' }],
      limit: 5,
      total_rows: 1,
      current_page: 1,
      next_url: 'next',
      prev_url: 'prev'
    } as any));

    await component.getContent(newDataset);

    expect(component.data.fiche.nextUrl).toBe('next');
    expect(component.data.pagination.perPage).toBe(5);
  });

  it('should update pagination nextUrl on pageChange when nextUrl exists', async () => {
    component.data.fiche.nextUrl = 'next';
    component.data.fiche.prevUrl = 'prev';
    spyOn(component, 'getContent').and.returnValue(Promise.resolve());

    await component.pageChange({ pageIndex: 1, pageSize: 5, previousPageIndex: 0 } as any);

    expect(component.data.pagination.nextUrl).toBe('next');
    expect(component.data.pagination.page).toBe(2);
    expect(component.data.pagination.perPage).toBe(5);
  });

  it('should reject getContent when response is empty and reset render state', async () => {
    spyOn(window, 'alert');
    datasetServiceSpy.getContentDataset.and.returnValue(of(null as any));

    await expectAsync(component.getContent()).toBeRejected();
    expect(component.data.displayedColumns).toEqual([]);
    expect(component.data.renderTabIndex).toBe(0);
    expect(window.alert).toHaveBeenCalledWith('Connection successful but unable to get data.');
  });

  it('should reset state when response has no data for a new dataset', async () => {
    spyOn(window, 'alert');
    datasetServiceSpy.getContentDataset.and.returnValue(of({} as any));
    const newDataset = { name: 'New Dataset', id: 'new-id' } as any;

    await component.getContent(newDataset);

    expect(component.data.displayedColumns).toEqual([]);
    expect(component.data.renderTabIndex).toBe(0);
    expect(window.alert).not.toHaveBeenCalled();
  });

  it('should apply filter text from event', () => {
    component.applyFilter({ target: { value: '  Test  ' } } as any);

    expect(component.filterTables).toBe('test');
  });

  it('should toggle active table-name class on selectedDataset event', () => {
    const first = document.createElement('div');
    const second = document.createElement('div');
    first.classList.add('table-name');
    second.classList.add('table-name');
    document.body.appendChild(first);
    document.body.appendChild(second);

    component.selectedDataset({ target: second } as any);

    expect(first.classList.contains('active-dataset')).toBeFalse();
    expect(second.classList.contains('active-dataset')).toBeTrue();

    document.body.removeChild(first);
    document.body.removeChild(second);
  });

  it('should set the databases and collections of a Mongo response', async () => {
    datasetServiceSpy.getContentDataset.and.returnValue(of({
      data: [],
      databases: ['shop', 'crm'],
      collections: [['orders'], ['contacts']]
    } as any));

    await component.getContent({ name: 'Mongo', id: 'mongo-id' } as any);

    expect(component.data.dbNames).toEqual(['shop', 'crm']);
    expect(component.data.tableNames).toEqual([['orders'], ['contacts']] as any);
    expect(component.data.fiche.items).toEqual([]);
    expect(component.data.displayedColumns).toEqual([' ']);
  });

  it('should set the indices of an Elasticsearch response and send the index apart', async () => {
    component.data.datasetParams = { database: 'db', table: 'logs-2025' };
    datasetServiceSpy.getContentDataset.and.returnValue(of({ data: [], indices: ['logs-2025', 'metrics'] } as any));
    const elastic = { name: 'Elastic', id: 'es-id', type: 'elastic' } as any;

    await component.getContent(elastic);

    expect(datasetServiceSpy.getContentDataset).toHaveBeenCalledWith(elastic, component.data.pagination, { index: 'logs-2025' } as any);
    expect(component.data.dbNames).toBeNull();
    expect(component.data.tableNames).toEqual(['logs-2025', 'metrics']);
    expect(component.data.displayedColumns).toEqual([' ']);
  });

  it('should send a null index for an Elasticsearch dataset without table', async () => {
    datasetServiceSpy.getContentDataset.and.returnValue(of({ data: [], indices: [] } as any));
    const elastic = { name: 'Elastic', id: 'es-id', type: 'elastic' } as any;

    await component.getContent(elastic);

    expect(datasetServiceSpy.getContentDataset).toHaveBeenCalledWith(elastic, component.data.pagination, { index: null } as any);
  });

  it('should keep the names and use the columns of the first item for the same dataset', async () => {
    component.data.dbNames = ['kept'];
    component.data.tableNames = ['kept-table'];
    datasetServiceSpy.getContentDataset.and.returnValue(of({
      data: [{ a: 1, b: 2 }, { c: 3 }],
      limit: 10,
      total_rows: 2,
      current_page: 0,
      databases: ['other']
    } as any));

    await component.getContent();

    expect(datasetServiceSpy.getContentDataset).toHaveBeenCalledWith(
      component.data.selectedDataset, component.data.pagination, { database: '', table: '' });
    expect(component.data.dbNames).toEqual(['kept']);
    expect(component.data.tableNames).toEqual(['kept-table']);
    expect(component.data.fiche).toEqual({ items: [{ a: 1, b: 2 }, { c: 3 }], limit: 10, total: 2, current_page: 0 } as any);
    expect(component.data.displayedColumns).toEqual(['a', 'b']);
  });

  it('should reset the names for a new dataset that is not a database', async () => {
    component.data.dbNames = ['old'];
    component.data.tableNames = ['old-table'];
    datasetServiceSpy.getContentDataset.and.returnValue(of({ data: [{ x: 1 }], total_rows: 1 } as any));

    await component.getContent({ name: 'File', id: 'file-id' } as any);

    expect(component.data.dbNames).toBeNull();
    expect(component.data.tableNames).toBeNull();
    expect(component.data.displayedColumns).toEqual(['x']);
  });

  it('should keep the displayed columns for an empty single table', async () => {
    component.data.dbNames = null;
    component.data.tableNames = null;
    component.data.displayedColumns = ['previous'];
    datasetServiceSpy.getContentDataset.and.returnValue(of({ data: [], total_rows: 0 } as any));

    await component.getContent();

    expect(component.data.fiche.items).toEqual([]);
    expect(component.data.displayedColumns).toEqual(['previous']);
  });

  it('should keep the page size when the API response has no limit, and clear the next URL of the request', async () => {
    component.data.pagination.nextUrl = 'requested';
    datasetServiceSpy.getContentDataset.and.returnValue(of({
      data: [{ col1: 'val' }],
      limit: 0,
      next_url: null,
      prev_url: 'prev'
    } as any));

    await component.getContent();

    expect(component.data.pagination.nextUrl).toBeNull();
    expect(component.data.pagination.perPage).toBe(100);
    expect(component.data.fiche.nextUrl).toBeNull();
    expect(component.data.fiche.prevUrl).toBe('prev');
  });

  it('should reject getContent on service error', async () => {
    datasetServiceSpy.getContentDataset.and.returnValue(throwError(() => new Error('fail')));

    await expectAsync(component.getContent()).toBeRejected();
    expect(component.data.pagination.nextUrl).toBeNull();
  });
});
