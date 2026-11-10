import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { TransformationModalComponent } from './transformation-modal.component';

describe('TransformationModalComponent', () => {
  let component: TransformationModalComponent;
  let fixture: ComponentFixture<TransformationModalComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [IonicModule.forRoot(), TransformationModalComponent]
}).compileComponents();

    fixture = TestBed.createComponent(TransformationModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
