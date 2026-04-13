import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { NO_ERRORS_SCHEMA, Component, Input } from '@angular/core';
import { DatasetsComponent } from './datasets.component';
import { LoadingService } from 'src/app/services/loading.service';
import { Dataset } from 'src/app/models/dataset';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

// Stub du composant datasets-modal pour éviter le problème de propriété read-only
@Component({
    selector: 'app-datasets-modal',
    template: '',
    standalone: false
})
class DatasetsModalStubComponent {
  @Input() dataset: Dataset | null = null;
  modal = { isOpen: false };
}

describe('DatasetsComponent', () => {
  let component: DatasetsComponent;
  let fixture: ComponentFixture<DatasetsComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    declarations: [DatasetsComponent, DatasetsModalStubComponent],
    schemas: [NO_ERRORS_SCHEMA],
    imports: [IonicModule.forRoot()],
    providers: [
        { provide: LoadingService, useValue: jasmine.createSpyObj('LoadingService', ['show', 'hide']) },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
    ]
}).compileComponents();

    fixture = TestBed.createComponent(DatasetsComponent);
    component = fixture.componentInstance;
  }));

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });
});
