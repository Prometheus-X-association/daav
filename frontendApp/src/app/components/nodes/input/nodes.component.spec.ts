import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { ClassicPreset } from 'rete';
import { InputNodeComponent } from './nodes.component';

describe('NodesComponent', () => {
  let component: InputNodeComponent;
  let fixture: ComponentFixture<InputNodeComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [IonicModule.forRoot(), InputNodeComponent]
}).compileComponents();

    fixture = TestBed.createComponent(InputNodeComponent);
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
