import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { MainPage } from './main.page';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { LoadingService } from '../services/loading.service';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('MainPage', () => {
  let component: MainPage;
  let fixture: ComponentFixture<MainPage>;

  beforeEach(async () => {
    const loadingServiceSpy = jasmine.createSpyObj('LoadingService', ['show', 'hide']);

    await TestBed.configureTestingModule({
    declarations: [MainPage],
    schemas: [CUSTOM_ELEMENTS_SCHEMA],
    imports: [IonicModule.forRoot()],
    providers: [
        { provide: LoadingService, useValue: loadingServiceSpy },
        provideHttpClient(withInterceptorsFromDi()),
        provideHttpClientTesting()
    ]
}).compileComponents();

    fixture = TestBed.createComponent(MainPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should only collapse the side panel while a workflow is open', () => {
    component.toggleSidePanel();

    expect(component.isSidePanelCollapsed).toBe(false);

    component.matTabIndex = 2;
    component.transformationView = 'rete';

    expect(component.isWorkflowOpen).toBe(true);
    expect(component.isSidePanelCollapsed).toBe(true);
  });

  it('should go back to the workflow list and expand the side panel when the workflow is closed', () => {
    component.matTabIndex = 2;
    component.transformationView = 'rete';
    component.loadProjectId = 'project-1';
    component.toggleSidePanel();

    component.closeWorkflow();

    expect(component.transformationView).toBe('list');
    expect(component.loadProjectId).toBeUndefined();
    expect(component.isSidePanelCollapsed).toBe(false);
  });

  it('should not reopen the last loaded workflow when creating a new one from the list', () => {
    component.loadProjectId = 'project-1';

    component.createWorkflow();

    expect(component.loadProjectId).toBeUndefined();
  });
});
