import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TransformationComponent } from './transformation.component';
import { LoadingService } from 'src/app/services/loading.service';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('TransformationComponent', () => {
  let component: TransformationComponent;
  let fixture: ComponentFixture<TransformationComponent>;

  beforeEach(waitForAsync(() => {
    const loadingSpy = jasmine.createSpyObj('LoadingService', ['present', 'dismiss']);

    TestBed.configureTestingModule({
    declarations: [TransformationComponent],
    imports: [IonicModule.forRoot()],
    providers: [
        { provide: LoadingService, useValue: loadingSpy },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
    ]
}).compileComponents();

    fixture = TestBed.createComponent(TransformationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
