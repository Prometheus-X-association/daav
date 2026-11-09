import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { MatDialog } from '@angular/material/dialog';
import { of, throwError } from 'rxjs';
import { ElasticDashboardComponent } from './elastic-dashboard.component';
import { ElasticService } from 'src/app/services/elastic.service';
import { DatasetElasticSearch } from 'src/app/models/dataset-elastic-search';

describe('ElasticDashboardComponent', () => {
  let fixture: ComponentFixture<ElasticDashboardComponent>;
  let component: ElasticDashboardComponent;
  let elastic: jasmine.SpyObj<ElasticService>;

  const indices = [
    { index: 'customers', health: 'green', status: 'open', docsCount: 20, sizeBytes: 2048, primaries: 1, replicas: 0, aliases: [] },
    { index: 'products', health: 'green', status: 'open', docsCount: 50, sizeBytes: 4096, primaries: 1, replicas: 0, aliases: ['shop'] },
  ] as any[];

  function create(datasetValues: any = {}) {
    fixture = TestBed.createComponent(ElasticDashboardComponent);
    component = fixture.componentInstance;
    component.dataset = new DatasetElasticSearch({
      id: 'ds1', name: 'es', type: 'elastic', url: 'http://es:9200/', user: 'elastic', ...datasetValues,
    } as any);
    fixture.detectChanges();
  }

  beforeEach(async () => {
    elastic = jasmine.createSpyObj('ElasticService', ['getInfo', 'getIndices', 'getMapping', 'query', 'createIndex']);
    elastic.getInfo.and.returnValue(of({ clusterName: 'c', version: '8.15.5', status: 'green', numberOfNodes: 1 } as any));
    elastic.getIndices.and.returnValue(of(indices));
    elastic.getMapping.and.returnValue(of({ properties: { sku: { type: 'keyword' } } }));
    elastic.query.and.returnValue(of({ total: 50, data: [{ _id: '1', sku: 'A' }, { _id: '2', price: 3 }] }));
    elastic.createIndex.and.returnValue(of({ index: 'new', created: true }));

    await TestBed.configureTestingModule({
      imports: [ElasticDashboardComponent],
      providers: [
        { provide: ElasticService, useValue: elastic },
        { provide: MatDialog, useValue: {} },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting(),
      ],
    }).compileComponents();
  });

  it('should load the cluster information and indices', () => {
    create();
    expect(component.info.version).toBe('8.15.5');
    expect(component.totalDocs).toBe(70);
    expect(fixture.nativeElement.querySelectorAll('table.indices tbody tr').length).toBe(2);
  });

  it('should filter indices by name or alias', () => {
    create();
    component.indexFilter = 'shop';
    expect(component.filteredIndices.map((i) => i.index)).toEqual(['products']);
  });

  it('should select the dataset index automatically', () => {
    create({ index: 'products' });
    expect(component.selectedIndex.index).toBe('products');
    expect(elastic.getMapping).toHaveBeenCalledWith('ds1', 'products');
    expect(elastic.query).toHaveBeenCalled();
  });

  it('should run a query and list all result columns', () => {
    create();
    component.selectIndex(indices[1]);
    component.queryText = ' category:books ';
    component.runQuery(2);
    expect(elastic.query).toHaveBeenCalledWith('ds1', { index: 'products', query: 'category:books', page: 2, size: 20 });
    expect(component.queryColumns).toEqual(['_id', 'sku', 'price']);
    expect(component.queryPageCount).toBe(3);
  });

  it('should show the query error', () => {
    create();
    elastic.query.and.returnValue(throwError(() => ({ error: { detail: 'Invalid JSON query' } })));
    component.selectIndex(indices[1]);
    expect(component.queryError).toBe('Invalid JSON query');
  });

  it('should give the delete command without secrets', () => {
    create({ authMode: 'apiKey' });
    component.selectIndex(indices[1]);
    expect(component.deleteCommand).toBe('curl -X DELETE -H "Authorization: ApiKey <api-key>" "http://es:9200/products"');
    component.dataset.authMode = 'basic';
    expect(component.deleteCommand).toBe('curl -X DELETE -u elastic "http://es:9200/products"');
  });

  it('should create an index with mappings', () => {
    create();
    component.newIndexName = 'new';
    component.newIndexMappings = '{"properties": {}}';
    component.createIndex();
    expect(elastic.createIndex).toHaveBeenCalledWith('ds1', 'new', { properties: {} });
    expect(component.createMessage).toContain('new');
    expect(elastic.getIndices).toHaveBeenCalledTimes(2);
  });

  it('should refuse invalid mappings', () => {
    create();
    component.newIndexName = 'new';
    component.newIndexMappings = '{bad';
    component.createIndex();
    expect(elastic.createIndex).not.toHaveBeenCalled();
    expect(component.createError).toContain('not valid JSON');
  });
});
