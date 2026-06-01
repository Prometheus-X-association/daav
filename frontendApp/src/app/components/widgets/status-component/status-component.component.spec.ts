import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { IonicModule } from '@ionic/angular';
import { MatTooltip, MatTooltipModule } from '@angular/material/tooltip';
import { StatusComponentComponent } from './status-component.component';
import { StatusControl } from './status-component.component';
import { StatusNode } from 'src/app/enums/status-node';

describe('StatusComponentComponent', () => {
  let component: StatusComponentComponent;
  let fixture: ComponentFixture<StatusComponentComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ StatusComponentComponent ],
      imports: [IonicModule.forRoot(), MatTooltipModule]
    }).compileComponents();

    fixture = TestBed.createComponent(StatusComponentComponent);
      component = fixture.componentInstance;
    component.data = new StatusControl(StatusNode.Valid, 'Test message', []);
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render tooltip with the status message', () => {
    const circle = fixture.debugElement.query(By.css('.circle'));
    expect(circle).toBeTruthy();

    const tooltip = circle.injector.get(MatTooltip);
    expect(tooltip.message).toBe('Test message');
  });

  it('should show stack trace button when status is Error and open modal on click', () => {
    component.data = new StatusControl(StatusNode.Error, 'Failed to execute', ['stack line 1']);
    fixture.detectChanges();

    const button = fixture.debugElement.query(By.css('ion-button'));
    expect(button).toBeTruthy();
    expect(button.nativeElement.textContent.trim()).toBe('Stack Trace');

    expect(component.isModalOpen).toBeFalse();
    button.nativeElement.click();
    fixture.detectChanges();
    expect(component.isModalOpen).toBeTrue();
  });
});
