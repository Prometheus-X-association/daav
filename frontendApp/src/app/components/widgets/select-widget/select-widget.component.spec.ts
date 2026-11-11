import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { MatSelect, MatSelectModule } from '@angular/material/select';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { By } from '@angular/platform-browser';
import { SelectWidgetComponent, SelectControl } from './select-widget.component';

describe('SelectWidgetComponent', () => {
  let component: SelectWidgetComponent;
  let fixture: ComponentFixture<SelectWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [MatSelectModule, BrowserAnimationsModule, SelectWidgetComponent],
    providers: [provideIonicAngular()]
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

  it('should keep the none and new options of the control data', () => {
    const control = new SelectControl({ value: null, list: [], none: true, new: true });
    expect(control.none).toBeTrue();
    expect(control.new).toBeTrue();

    const noneOnly = new SelectControl({ value: null, list: [], none: true });
    expect(noneOnly.none).toBeTrue();
    expect(noneOnly.new).toBeFalse();

    const newOnly = new SelectControl({ value: null, list: [], new: true });
    expect(newOnly.none).toBeFalse();
    expect(newOnly.new).toBeTrue();
  });

  it('should list the None and New options before the items when enabled', () => {
    const openedOptions = (data: SelectControl): string[] => {
      fixture.componentRef.setInput('data', data);
      fixture.detectChanges();
      const select = fixture.debugElement.query(By.directive(MatSelect)).componentInstance as MatSelect;
      select.open();
      fixture.detectChanges();
      const labels = select.options.map(option => option.viewValue);
      select.close();
      fixture.detectChanges();
      return labels;
    };

    expect(openedOptions(new SelectControl({ value: null, list: [{ label: 'A', value: 'a' }], none: true })))
      .toEqual(['None', 'A']);
    expect(openedOptions(new SelectControl({ value: null, list: [{ label: 'A', value: 'a' }], new: true })))
      .toEqual(['New', 'A']);
    expect(openedOptions(new SelectControl({ value: null, list: [{ label: 'A', value: 'a' }] })))
      .toEqual(['A']);
  });
});
