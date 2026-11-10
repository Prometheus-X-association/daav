import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
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
    imports: [IonicModule.forRoot(), FormsModule, MatAutocompleteModule, MatFormFieldModule, MatInputModule, BrowserAnimationsModule, InputAutoCompleteWidgetComponent]
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
