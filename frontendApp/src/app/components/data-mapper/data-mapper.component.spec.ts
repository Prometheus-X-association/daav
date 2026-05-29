import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

import { DataMapperComponent } from './data-mapper.component';

describe('DataMapperComponent', () => {
  let component: DataMapperComponent;
  let fixture: ComponentFixture<DataMapperComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DataMapperComponent ],
      imports: [IonicModule.forRoot(), DragDropModule, MatCardModule, MatIconModule, MatTooltipModule]
    }).compileComponents();

    fixture = TestBed.createComponent(DataMapperComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should return connected lists from mappings', () => {
    component.mappings = [
      { id: 'map1', sources: [], targetName: 'target' }
    ];

    expect(component.getConnectedLists()).toEqual(['mapping-dropzone', 'mapping-map1']);
  });

  it('should set dragged column on drag start and reset on drag end', () => {
    const column = { id: 'col1', name: 'Column 1', type: 'string' } as any;

    component.onDragStart({} as any, column);

    expect(component.draggedColumn).toBe(column);

    component.onDragEnd();

    expect(component.draggedColumn).toBeNull();
    expect(component.activeMapping).toBeNull();
  });

  it('should move item within same container on drop', () => {
    const columnA = { id: 'a', name: 'A', type: 'string' } as any;
    const columnB = { id: 'b', name: 'B', type: 'string' } as any;
    const data = [columnA, columnB];
    const container = { data } as any;
    const event = {
      item: { data: columnA },
      previousContainer: container,
      container,
      previousIndex: 0,
      currentIndex: 1
    } as any;

    component.onDrop(event);

    expect(data[0]).toEqual(columnB);
    expect(data[1]).toEqual(columnA);
  });

  it('should add a source to an existing mapping on drop with targetMappingId', () => {
    const column = { id: 'col1', name: 'Column 1', type: 'string' } as any;
    component.mappings = [
      { id: 'map1', sources: [], targetName: 'Target 1' }
    ];

    const event = {
      item: { data: column },
      previousContainer: {} as any,
      container: {} as any
    } as any;

    component.onDrop(event, 'map1');

    expect(component.mappings[0].sources).toContain(column);
  });

  it('should create a new mapping on drop without targetMappingId', () => {
    const column = { id: 'col2', name: 'Column 2', type: 'string' } as any;
    spyOn(window.crypto, 'randomUUID').and.returnValue('00000000-0000-0000-0000-000000000000');

    const event = {
      item: { data: column },
      previousContainer: {} as any,
      container: {} as any
    } as any;

    component.onDrop(event);

    expect(component.mappings.length).toBe(1);
    expect(component.mappings[0].id).toBe('00000000-0000-0000-0000-000000000000');
    expect(component.mappings[0].sources).toContain(column);
  });

  it('should identify mapped columns and dataset names', () => {
    const column = { id: 'col1', name: 'Column 1', type: 'string' } as any;
    component.datasets = [{ id: 'ds1', name: 'Dataset 1', columns: [] } as any];
    component.mappings = [{ id: 'map1', sources: [column], targetName: 'Target 1' } as any];

    expect(component.isColumnMapped(column)).toBeTrue();
    expect(component.getDatasetName('ds1')).toBe('Dataset 1');
    expect(component.getDatasetName('unknown')).toBe('');
  });

  it('should remove mapping and remove source from mapping when empty', () => {
    component.mappings = [
      { id: 'map1', sources: [{ id: 'col1', name: 'Column 1', type: 'string' }], targetName: 'Target 1' } as any
    ];

    component.removeSourceFromMapping('map1', 'col1');

    expect(component.mappings.length).toBe(0);
  });

  it('should toggle collapse state for sections', () => {
    expect(component.isSectionCollapsed('sectionA')).toBeFalse();

    component.toggleSection('sectionA');
    expect(component.isSectionCollapsed('sectionA')).toBeTrue();

    component.toggleSection('sectionA');
    expect(component.isSectionCollapsed('sectionA')).toBeFalse();
  });
});
