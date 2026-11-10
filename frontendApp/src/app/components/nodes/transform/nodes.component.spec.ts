import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { ClassicPreset } from 'rete';
import { TransformNodeComponent } from './nodes.component';

describe('NodesComponent', () => {
  let component: TransformNodeComponent;
  let fixture: ComponentFixture<TransformNodeComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [TransformNodeComponent],
    providers: [provideIonicAngular()]
}).compileComponents();

    fixture = TestBed.createComponent(TransformNodeComponent);
    component = fixture.componentInstance;
    component.data = new ClassicPreset.Node('test');
    component.data.selected = false;
    component.emit = jasmine.createSpy('emit');
    component.rendered = jasmine.createSpy('rendered');
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
