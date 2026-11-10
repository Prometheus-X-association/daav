import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { LoadingComponent } from './loading.component';
import { LoadingService } from 'src/app/services/loading.service';

describe('LoadingComponent', () => {
  let component: LoadingComponent;
  let fixture: ComponentFixture<LoadingComponent>;

  beforeEach(waitForAsync(() => {
    const mockLoadingService = jasmine.createSpyObj('LoadingService', ['show', 'hide', 'loading']);
    mockLoadingService.loading.and.returnValue(false);

    TestBed.configureTestingModule({
      imports: [LoadingComponent],
      providers: [
        provideIonicAngular(),
        { provide: LoadingService, useValue: mockLoadingService }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LoadingComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
