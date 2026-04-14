import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { provideHttpClientTesting } from '@angular/common/http/testing';

import { DatasetsModalComponent } from './datasets-modal.component';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('DatasetsModalComponent', () => {
  let component: DatasetsModalComponent;
  let fixture: ComponentFixture<DatasetsModalComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    declarations: [DatasetsModalComponent],
    imports: [IonicModule.forRoot()],
    providers: [provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()]
}).compileComponents();

    fixture = TestBed.createComponent(DatasetsModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
