import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { PTXDashboardComponent } from './ptxdashboard.component';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';

describe('PTXDashboardComponent', () => {
  let component: PTXDashboardComponent;
  let fixture: ComponentFixture<PTXDashboardComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [IonicModule.forRoot(), PTXDashboardComponent],
    providers: [provideHttpClient(withInterceptorsFromDi()), provideHttpClientTesting()]
}).compileComponents();

    fixture = TestBed.createComponent(PTXDashboardComponent);
    component = fixture.componentInstance;
    component.dataset = { id: 'test', name: 'test' } as any; // Mock input data
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should compute card class and skeleton array', () => {
    expect(component.getCardClass('ptx:serviceofferings')).toBe('card-service');
    expect(component.getCardClass('ptx:softwaresources')).toBe('card-software');
    expect(component.getCardClass('ptx:dataresources')).toBe('card-data');
    expect(component.getCardClass('unknown')).toBe('card-default');
    expect(component.getSkeletonArray(4)).toEqual([0, 1, 2, 3]);
  });

  it('should toggle executions visibility and count hidden executions', () => {
    const exchange = {
      executions: Array.from({ length: 12 }, (_, i) => ({ id: `e${i}`, createdAt: `2024-05-${i + 1}T12:00:00Z` }))
    } as any;

    expect(component.shouldShowMoreButton(exchange)).toBeTrue();
    expect(component.getHiddenExecutionsCount(exchange)).toBe(2);
    expect(component.getExecutionsToShow(exchange, 0).length).toBe(10);

    component.toggleShowAllExecutions(0);
    expect(component.isShowingAllExecutions(0)).toBeTrue();
    expect(component.getExecutionsToShow(exchange, 0).length).toBe(12);

    component.toggleShowAllExecutions(0);
    expect(component.isShowingAllExecutions(0)).toBeFalse();
  });

  it('should toggle exchange expanded state and count executions', () => {
    const exchange = { executions: [{ id: 'x1' }, { id: 'x2' }] } as any;

    expect(component.isExchangeExpanded(1)).toBeFalse();
    component.toggleExchange(1);
    expect(component.isExchangeExpanded(1)).toBeTrue();
    component.toggleExchange(1);
    expect(component.isExchangeExpanded(1)).toBeFalse();

    expect(component.getExecutionCount(exchange)).toBe(2);
  });

  it('should return latest execution date and handle no executions', () => {
    expect(component.getLatestExecutionDate({ executions: [] } as any)).toBe('No executions');

    const latest = component.getLatestExecutionDate({
      executions: [
        { id: '1', createdAt: '2024-05-01T12:00:00Z' },
        { id: '2', createdAt: '2024-05-02T18:30:00Z' }
      ]
    } as any);

    expect(latest).toContain('mai');
    expect(component.formatDate('')).toBe('N/A');
  });
});
