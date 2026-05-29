import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { DataFilterComponent } from './data-filter.component';

describe('DataFilterComponent', () => {
  let component: DataFilterComponent;
  let fixture: ComponentFixture<DataFilterComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DataFilterComponent ],
      imports: [IonicModule.forRoot()],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(DataFilterComponent);
    component = fixture.componentInstance;
    component.filterControl = { query: {}, config: {} } as any; // Mock input data
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize query config and default condition on init', () => {
    component.datasets = [
      {
        id: 'ds1',
        name: 'Dataset 1',
        columns: [
          { id: 'c1', name: 'Column 1', type: 'string' },
          { id: 'c2', name: 'Column 2', type: 'number' },
          { id: 'c3', name: 'Column 3', type: 'date' },
          { id: 'c4', name: 'Column 4', type: 'boolean' }
        ]
      } as any
    ];
    component.filterControl = { query: {}, config: {} } as any;

    component.ngOnInit();

    expect(component.query.condition).toBe('and');
    expect(component.config.fields['c1'].type).toBe('string');
    expect(component.config.fields['c2'].type).toBe('number');
    expect(component.config.fields['c3'].type).toBe('date');
    expect(component.config.fields['c4'].type).toBe('boolean');
  });

  it('should allow query getter and setter to work', () => {
    component.filterControl = { query: { condition: 'or' }, config: {} } as any;

    expect(component.query.condition).toBe('or');

    component.query = { condition: 'and' } as any;
    expect(component.filterControl.query.condition).toBe('and');
  });
});
