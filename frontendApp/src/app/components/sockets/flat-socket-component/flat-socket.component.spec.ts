import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { FlatSocketComponent } from './flat-socket.component';

describe('FlatSocketComponent', () => {
  let component: FlatSocketComponent;
  let fixture: ComponentFixture<FlatSocketComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [FlatSocketComponent, IonicModule.forRoot()]
}).compileComponents();

    fixture = TestBed.createComponent(FlatSocketComponent);
    component = fixture.componentInstance;
    component.data = { name: 'test-socket' };
    component.rendered = jasmine.createSpy('rendered');
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
