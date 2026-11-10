import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { ClassicPreset } from 'rete';
import { OutputNodeComponent } from './nodes.component';

describe('NodesComponent', () => {
  let component: OutputNodeComponent;
  let fixture: ComponentFixture<OutputNodeComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [IonicModule.forRoot(), OutputNodeComponent]
}).compileComponents();

    fixture = TestBed.createComponent(OutputNodeComponent);
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
