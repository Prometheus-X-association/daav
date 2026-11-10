import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { ButtonWidgetComponent, ButtonControl } from '../button-widget/button-widget.component';

describe('ButtonComponent', () => {
  let component: ButtonWidgetComponent;
  let fixture: ComponentFixture<ButtonWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [ButtonWidgetComponent],
    providers: [provideIonicAngular()]
}).compileComponents();

    fixture = TestBed.createComponent(ButtonWidgetComponent);
    component = fixture.componentInstance;
    component.data = new ButtonControl(() => {}, 'Test Button');
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should call data.onClick when button is clicked', () => {
    const spy = jasmine.createSpy('onClick');
    component.data = new ButtonControl(spy, 'Click me');
    fixture.detectChanges();
    const btn: HTMLButtonElement | null = fixture.nativeElement.querySelector('button');
    expect(btn).toBeTruthy();
    btn!.click();
    expect(spy).toHaveBeenCalled();
  });
});
