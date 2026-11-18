import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { FormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { InputAutoCompleteWidgetComponent, InputAutoCompleteControl } from './input-auto-complete-widget.component';

describe('InputAutoCompleteWidgetComponent', () => {
  let component: InputAutoCompleteWidgetComponent;
  let fixture: ComponentFixture<InputAutoCompleteWidgetComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
    imports: [FormsModule, MatAutocompleteModule, MatFormFieldModule, MatInputModule, BrowserAnimationsModule, InputAutoCompleteWidgetComponent],
    providers: [provideIonicAngular()]
}).compileComponents();

    fixture = TestBed.createComponent(InputAutoCompleteWidgetComponent);
    component = fixture.componentInstance;
    component.data = new InputAutoCompleteControl({ value: 'test', list: ['test1', 'test2'], type: 'text' });
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
