import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { NodeLoaderWidgetComponent } from './node-loader-widget.component';

describe('NodeLoaderWidgetComponent', () => {
  let component: NodeLoaderWidgetComponent;
  let fixture: ComponentFixture<NodeLoaderWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ NodeLoaderWidgetComponent ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(NodeLoaderWidgetComponent);
    component = fixture.componentInstance;
    component.data = { id: 'test-loader', loading: false } as any; // Mock input data
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('ngOnChanges should call detectChanges on cdr', () => {
    spyOn(component.cdr, 'detectChanges');
    component.ngOnChanges({} as any);
    expect(component.cdr.detectChanges).toHaveBeenCalled();
  });
});
