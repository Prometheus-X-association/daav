import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
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
      declarations: [RenderComponent],
      schemas: [NO_ERRORS_SCHEMA],
      imports: [IonicModule.forRoot(), MatTabsModule, BrowserAnimationsModule],
      providers: [
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
      fiche: { items: [], limit: 10, total: 0, current_page: 1 } as any,
      selectedDataset: { name: 'Test Dataset', id: 'test-id' } as any,
      renderTabIndex: 0,
      pagination: { perPage: 100, page: 1 } as any,
      datasetParams: { database: '', table: '' }
    } as any;
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

  it('should reject getContent on service error', async () => {
    datasetServiceSpy.getContentDataset.and.returnValue(throwError(() => new Error('fail')));

    await expectAsync(component.getContent()).toBeRejected();
    expect(component.data.pagination.nextUrl).toBeNull();
  });
});
