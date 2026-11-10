import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { GlobalSocketComponent } from './global-socket.component';

describe('GlobalSocketComponent', () => {
  let component: GlobalSocketComponent;
  let fixture: ComponentFixture<GlobalSocketComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [GlobalSocketComponent, IonicModule.forRoot()]
}).compileComponents();

    fixture = TestBed.createComponent(GlobalSocketComponent);
    component = fixture.componentInstance;
    component.data = { name: 'test-socket' };
    component.rendered = jasmine.createSpy('rendered');
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
