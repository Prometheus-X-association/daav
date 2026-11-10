import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA, Component, Input } from '@angular/core';
import { DatasetsComponent } from './datasets.component';
import { LoadingService } from 'src/app/services/loading.service';
import { Dataset } from 'src/app/models/dataset';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

// Stub du composant datasets-modal pour éviter le problème de propriété read-only
@Component({
    selector: 'app-datasets-modal',
    template: ''
})
class DatasetsModalStubComponent {
  @Input() dataset: Dataset | null = null;
  modal = { isOpen: false };
}

describe('DatasetsComponent', () => {
  let component: DatasetsComponent;
  let fixture: ComponentFixture<DatasetsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    schemas: [NO_ERRORS_SCHEMA],
    imports: [DatasetsComponent, DatasetsModalStubComponent],
    providers: [
        provideIonicAngular(),
        { provide: LoadingService, useValue: jasmine.createSpyObj('LoadingService', ['show', 'hide']) },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
    ]
}).compileComponents();

    fixture = TestBed.createComponent(DatasetsComponent);
    component = fixture.componentInstance;
  }));

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should display the edit and delete icons at their full size', async () => {
    (component.datasetService as any).datasetsSignal.set([{ id: '1', name: 'Dataset 1', type: 'file' } as Dataset]);
    // The list is displayed in the narrow side menu: each action column is 10% of the row
    fixture.nativeElement.style.display = 'block';
    fixture.nativeElement.style.width = '300px';
    fixture.detectChanges();

    // The action buttons are revealed on hover and on keyboard focus (:focus-within): show them as the hover does
    const containers: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('.iconsContainer'));
    containers.forEach((container) => container.style.display = 'flex');
    await fixture.whenStable();

    const icons: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('.icon-button ion-icon'));
    expect(icons.length).toBe(2);
    for (const icon of icons) {
      expect(icon.getBoundingClientRect().width).toBeGreaterThanOrEqual(22);
    }
  });

  it('should open modal and set editDataset', () => {
    component.datasetModal = { modal: { isOpen: false } } as any;
    const dataset = { id: '1', name: 'Dataset 1' } as Dataset;

    component.openModal(dataset);

    expect(component.editDataset).toBe(dataset);
    expect(component.datasetModal.modal.isOpen).toBeTrue();
  });

  it('should emit dataset when selected', () => {
    spyOn(component.selectedDataset, 'emit');
    const dataset = { id: '2', name: 'Dataset 2' } as Dataset;

    component.selectDataset(dataset);

    expect(component.dataset).toBe(dataset);
    expect(component.selectedDataset.emit).toHaveBeenCalledWith(dataset);
  });

  it('should toggle active dataset class on event target', () => {
    const first = document.createElement('div');
    const second = document.createElement('div');
    first.classList.add('dataset-name');
    second.classList.add('dataset-name');
    document.body.appendChild(first);
    document.body.appendChild(second);

    component.activeDataset({ target: second } as any);

    expect(first.classList.contains('active-dataset')).toBeFalse();
    expect(second.classList.contains('active-dataset')).toBeTrue();

    document.body.removeChild(first);
    document.body.removeChild(second);
  });
});
