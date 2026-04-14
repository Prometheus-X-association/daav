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
});
