import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { DataMapperWidgetComponent, DataMapperControl } from './data-mapper-widget.component';
import { HasDatasetsPipe } from 'src/app/models/data-mapper-types';

describe('DataMapperWidgetComponent', () => {
  let component: DataMapperWidgetComponent;
  let fixture: ComponentFixture<DataMapperWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [DataMapperWidgetComponent, HasDatasetsPipe],
    providers: [provideIonicAngular()]
}).compileComponents();

    fixture = TestBed.createComponent(DataMapperWidgetComponent);
    component = fixture.componentInstance;
    component.data = new DataMapperControl([], []);
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should open modal and close on dismiss', () => {
    component.openModal();
    expect(component.isModalOpen).toBeTrue();

    const customEvent = { detail: { value: 'ok' } } as any;
    const callbackSpy = jasmine.createSpy('callback');
    component.data.callback = callbackSpy;

    component.onWillDismiss(customEvent);

    expect(component.isModalOpen).toBeFalse();
    expect(callbackSpy).toHaveBeenCalledWith(customEvent);
  });
});
