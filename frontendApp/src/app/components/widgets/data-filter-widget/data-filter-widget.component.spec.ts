import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { DataFilterWidgetComponent, DataFilterControl } from './data-filter-widget.component';
import { HasDatasetsPipe } from 'src/app/models/data-mapper-types';

describe('DataFilterWidgetComponent', () => {
  let component: DataFilterWidgetComponent;
  let fixture: ComponentFixture<DataFilterWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ DataFilterWidgetComponent, HasDatasetsPipe ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(DataFilterWidgetComponent);
    component = fixture.componentInstance;
    component.data = new DataFilterControl([]);
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

    component.onWillDismiss(customEvent as any);

    expect(component.isModalOpen).toBeFalse();
    expect(callbackSpy).toHaveBeenCalledWith(customEvent);
  });
});
