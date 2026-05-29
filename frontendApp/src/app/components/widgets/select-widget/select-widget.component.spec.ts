import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { MatSelectModule } from '@angular/material/select';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { SelectWidgetComponent, SelectControl } from './select-widget.component';

describe('SelectWidgetComponent', () => {
  let component: SelectWidgetComponent;
  let fixture: ComponentFixture<SelectWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SelectWidgetComponent ],
      imports: [IonicModule.forRoot(), MatSelectModule, BrowserAnimationsModule]
    }).compileComponents();

    fixture = TestBed.createComponent(SelectWidgetComponent);
    component = fixture.componentInstance;
    component.data = new SelectControl({ value: 'test', list: [{label: 'Test', value: 'test'}] });
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('onOpenedChange should store oldValue when opened', () => {
    component.data = new SelectControl({ value: 'a', list: [{label: 'A', value: 'a'}] });
    component.data.value = 'current';
    component.data.oldValue = 'old';
    component.onOpenedChange(true);
    expect(component.data.oldValue).toBe('current');
  });
});
