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

  it('should reject getContent on service error', async () => {
    datasetServiceSpy.getContentDataset.and.returnValue(throwError(() => new Error('fail')));

    await expectAsync(component.getContent()).toBeRejected();
    expect(component.data.pagination.nextUrl).toBeNull();
  });
});
