import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';

import { DeepSocketComponent } from './deep-socket.component';

describe('DeepSocketComponent', () => {
  let component: DeepSocketComponent;
  let fixture: ComponentFixture<DeepSocketComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [DeepSocketComponent],
    providers: [provideIonicAngular()]
}).compileComponents();

    fixture = TestBed.createComponent(DeepSocketComponent);
    component = fixture.componentInstance;
    component.data = { name: 'test-socket' };
    component.rendered = jasmine.createSpy('rendered');
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
