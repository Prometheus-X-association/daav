import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { CustomConnectionComponent } from './connections.component';

describe('CustomConnectionComponent', () => {
  let component: CustomConnectionComponent;
  let fixture: ComponentFixture<CustomConnectionComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ CustomConnectionComponent ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(CustomConnectionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should bind path attribute to svg path element', () => {
    const testPath = 'M0,0 L10,10';
    component.path = testPath;
    fixture.detectChanges();
    const pathEl: SVGPathElement | null = fixture.nativeElement.querySelector('path');
    expect(pathEl).toBeTruthy();
    expect(pathEl!.getAttribute('d')).toBe(testPath);
  });
});
