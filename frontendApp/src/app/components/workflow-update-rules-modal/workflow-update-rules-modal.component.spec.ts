import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { provideIonicAngular } from '@ionic/angular/standalone';
import { MatDialogRef } from '@angular/material/dialog';

import { WorkflowUpdateRulesModalComponent } from './workflow-update-rules-modal.component';

describe('WorkflowUpdateRulesModalComponent', () => {
  let component: WorkflowUpdateRulesModalComponent;
  let fixture: ComponentFixture<WorkflowUpdateRulesModalComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [WorkflowUpdateRulesModalComponent],
      providers: [
        provideIonicAngular(),
        { provide: MatDialogRef, useValue: jasmine.createSpyObj('MatDialogRef', ['close']) }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(WorkflowUpdateRulesModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
