import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { WorkflowPage } from './workflow.page';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('WorkflowPage', () => {
  let component: WorkflowPage;
  let fixture: ComponentFixture<WorkflowPage>;

  beforeEach(async () => {
    const activatedRouteSpy = {
      params: of({ id: 'test' }),
      snapshot: { params: { id: 'test' } },
      paramMap: of({ get: (key: string) => 'test' }),
      queryParams: of({ projectId: 'test' })
    };

    await TestBed.configureTestingModule({
    declarations: [WorkflowPage],
    imports: [IonicModule.forRoot()],
    providers: [
        { provide: ActivatedRoute, useValue: activatedRouteSpy },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
    ]
}).compileComponents();

    fixture = TestBed.createComponent(WorkflowPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
