import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { CheckboxWidgetComponent, CheckboxControl } from './checkbox-widget.component';

describe('CheckboxWidgetComponent', () => {
  let component: CheckboxWidgetComponent;
  let fixture: ComponentFixture<CheckboxWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CheckboxWidgetComponent ],
      imports: [IonicModule.forRoot(), MatCheckboxModule]
    }).compileComponents();

    fixture = TestBed.createComponent(CheckboxWidgetComponent);
    component = fixture.componentInstance;
    component.data = new CheckboxControl({ value: false, label: 'Test' });
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('onInputChange should update data.value and call callback', () => {
    let called = false;
    const cb = (ev?: any) => { called = true; };
    component.data = new CheckboxControl({ value: false, label: 'Test' }, cb as any);
    fixture.detectChanges();

    const changeEvent: any = { checked: true };
    component.onInputChange(changeEvent as any);
    expect(component.data.value).toBeTrue();
    expect(called).toBeTrue();
  });
});
