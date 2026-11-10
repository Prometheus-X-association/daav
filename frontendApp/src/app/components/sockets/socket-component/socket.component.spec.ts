import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { SocketComponent } from './socket.component';

describe('SocketComponent', () => {
  let component: SocketComponent;
  let fixture: ComponentFixture<SocketComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [SocketComponent, IonicModule.forRoot()]
}).compileComponents();

    fixture = TestBed.createComponent(SocketComponent);
    component = fixture.componentInstance;
    component.data = { name: 'test-socket' };
    component.rendered = jasmine.createSpy('rendered');
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
