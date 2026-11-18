import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';

import { FlatSocketComponent } from './flat-socket.component';

describe('FlatSocketComponent', () => {
  let component: FlatSocketComponent;
  let fixture: ComponentFixture<FlatSocketComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [FlatSocketComponent],
    providers: [provideIonicAngular()]
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
