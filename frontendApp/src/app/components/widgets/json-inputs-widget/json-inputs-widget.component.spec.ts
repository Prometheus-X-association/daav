import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { JsonInputsWidgetComponent, JsonInputsControl } from './json-inputs-widget.component';

describe('JsonInputsWidgetComponent', () => {
  let component: JsonInputsWidgetComponent;
  let fixture: ComponentFixture<JsonInputsWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ JsonInputsWidgetComponent ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(JsonInputsWidgetComponent);
    component = fixture.componentInstance;
    component.data = new JsonInputsControl([]);
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('makeOptions should return editor options with correct modes', () => {
    const opts = component.makeOptions();
    expect(opts).toBeDefined();
    expect(Array.isArray(opts.modes)).toBeTrue();
    expect(opts.modes).toEqual(jasmine.arrayContaining(['code', 'text', 'tree', 'view']));
  });

  it('openModal should set isModalOpen true and call detectChanges', () => {
    spyOn(component.cdr, 'detectChanges');
    component.data = new JsonInputsControl([]);
    component.openModal();
    expect(component.isModalOpen).toBeTrue();
    expect(component.hasChanged).toBeFalse();
    expect(component.cdr.detectChanges).toHaveBeenCalled();
  });

  it('addInputExample should add an entry and set hasChanged', () => {
    component.data = new JsonInputsControl([]);
    component.hasChanged = false;
    component.addInputExample();
    expect(component.data.inputsDataExample.length).toBe(1);
    expect(component.hasChanged).toBeTrue();
  });

  it('removeInputExample should remove the correct entry and set hasChanged', () => {
    component.data = new JsonInputsControl(['a','b','c']);
    component.hasChanged = false;
    component.removeInputExample(1);
    expect(component.data.inputsDataExample).toEqual(['a','c']);
    expect(component.hasChanged).toBeTrue();
  });

  it('onWillDismiss should set event.detail.data and call callback if present', () => {
    let callbackCalled = false;
    const mockCallback = (event?: any) => { callbackCalled = true; };
    component.data = new JsonInputsControl([], mockCallback as any);
    component.hasChanged = true;

    const event: any = { detail: { data: undefined } };
    component.onWillDismiss(event as any);

    expect(event.detail.data).toBeTrue();
    expect(component.isModalOpen).toBeFalse();
    expect(callbackCalled).toBeTrue();
  });
});
