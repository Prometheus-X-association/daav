import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { CommonModule } from '@angular/common';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { FileDashboardComponent } from './file-dashboard.component';
import { DatasetService } from 'src/app/services/dataset.service';

describe('FileDashboardComponent', () => {
  let component: FileDashboardComponent;
  let fixture: ComponentFixture<FileDashboardComponent>;
  let datasetServiceSpy: jasmine.SpyObj<DatasetService>;

  beforeEach(waitForAsync(() => {
    datasetServiceSpy = jasmine.createSpyObj('DatasetService', ['editDataset']);
    datasetServiceSpy.editDataset.and.returnValue(of({}));

    TestBed.configureTestingModule({
      declarations: [FileDashboardComponent],
      imports: [IonicModule.forRoot(), CommonModule, MatFormFieldModule, MatSelectModule, BrowserAnimationsModule, HttpClientTestingModule],
      providers: [{ provide: DatasetService, useValue: datasetServiceSpy }]
    }).compileComponents();
    fixture = TestBed.createComponent(FileDashboardComponent);
    component = fixture.componentInstance;
    component.dataset = { id: 'test', name: 'test', files: [], ifExist: undefined } as any;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default ifExist to replace when undefined on ngOnInit', () => {
    component.dataset.ifExist = undefined;

    component.ngOnInit();

    expect(component.dataset.ifExist).toBe('replace');
  });

  it('should update ifExist and call onDatasetChange', () => {
    spyOn(component, 'onDatasetChange');

    component.onIfExistChange('append');

    expect(component.dataset.ifExist).toBe('append');
    expect(component.onDatasetChange).toHaveBeenCalled();
  });

  it('should preserve ifExist when already defined', () => {
    component.dataset.ifExist = 'append';
    component.ngOnInit();
    expect(component.dataset.ifExist).toBe('append');
  });

  it('should call editDataset on dataset change success', () => {
    datasetServiceSpy.editDataset.and.returnValue(of(component.dataset));

    component.onDatasetChange();

    expect(datasetServiceSpy.editDataset).toHaveBeenCalledWith(component.dataset);
  });

  it('should handle editDataset error without throwing', () => {
    datasetServiceSpy.editDataset.and.returnValue(throwError(() => new Error('update failed')));
    spyOn(console, 'error');

    component.onDatasetChange();

    expect(datasetServiceSpy.editDataset).toHaveBeenCalledWith(component.dataset);
    expect(console.error).toHaveBeenCalled();
  });

  it('should format file size correctly', () => {
    expect(component.formatFileSize(0)).toBe('Unknown');
    expect(component.formatFileSize(1024)).toBe('1 KB');
    expect(component.formatFileSize(1048576)).toBe('1 MB');
  });

  it('should return a human readable delimiter display', () => {
    expect(component.getDelimiterDisplay(',')).toBe('Comma (,)');
    expect(component.getDelimiterDisplay(';')).toBe('Semicolon (;)');
    expect(component.getDelimiterDisplay('|')).toBe('Pipe (|)');
    expect(component.getDelimiterDisplay('\t')).toBe('Tab (\\t)');
    expect(component.getDelimiterDisplay('X')).toBe('X');
  });

  it('should return the correct dataset status, icon, and text', () => {
    component.dataset.filePath = undefined;
    component.dataset.metadata = undefined;
    expect(component.getDatasetStatus()).toBe('incomplete');
    expect(component.getStatusIcon()).toBe('error');
    expect(component.getDatasetStatusText()).toBe('Dataset Not Configured');

    component.dataset.filePath = 'path';
    component.dataset.metadata = undefined;
    expect(component.getDatasetStatus()).toBe('partial');
    expect(component.getStatusIcon()).toBe('warning');
    expect(component.getDatasetStatusText()).toBe('Configuration Incomplete');

    component.dataset.metadata = {} as any;
    expect(component.getDatasetStatus()).toBe('complete');
    expect(component.getStatusIcon()).toBe('check_circle');
    expect(component.getDatasetStatusText()).toBe('Dataset Ready');
  });
});
