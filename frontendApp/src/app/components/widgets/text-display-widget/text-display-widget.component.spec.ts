import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { TextDisplayWidgetComponent, TextDisplayControl } from './text-display-widget.component';

describe('TextDisplayWidgetComponent', () => {
  let component: TextDisplayWidgetComponent;
  let fixture: ComponentFixture<TextDisplayWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [TextDisplayWidgetComponent],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(TextDisplayWidgetComponent);
    component = fixture.componentInstance;
    component.data = new TextDisplayControl({ value: 'hello', copyable: true });
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call copyToClipboard when copyable and stop event propagation', () => {
    const event = jasmine.createSpyObj('event', ['stopPropagation']);
    spyOn(component.data, 'copyToClipboard');

    component.onCopy('hello', event as any);

    expect(event.stopPropagation).toHaveBeenCalled();
    expect(component.data.copyToClipboard).toHaveBeenCalledWith('hello', event as any);
  });

  it('should not call copyToClipboard when copyable is false', () => {
    component.data.copyable = false;
    const event = jasmine.createSpyObj('event', ['stopPropagation']);
    spyOn(component.data, 'copyToClipboard');

    component.onCopy('hello', event as any);

    expect(component.data.copyToClipboard).not.toHaveBeenCalled();
  });

  it('should use navigator.clipboard when copying text', async () => {
    const event = jasmine.createSpyObj('event', ['preventDefault', 'stopPropagation']);
    const clipboard = { writeText: jasmine.createSpy('writeText').and.returnValue(Promise.resolve()) };

    if (!navigator.clipboard) {
      (navigator as any).clipboard = clipboard;
    } else {
      spyOn(navigator.clipboard, 'writeText').and.returnValue(Promise.resolve());
    }

    component.data.copyable = true;
    await component.data.copyToClipboard('abc', event as any);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(event.stopPropagation).toHaveBeenCalled();
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('abc');
  });
});
