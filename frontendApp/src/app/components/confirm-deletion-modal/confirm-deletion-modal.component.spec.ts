import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';

import { ConfirmDeletionModalComponent } from './confirm-deletion-modal.component';

describe('ConfirmDeletionModalComponent', () => {
  let component: ConfirmDeletionModalComponent;
  let fixture: ComponentFixture<ConfirmDeletionModalComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      imports: [IonicModule.forRoot(), ConfirmDeletionModalComponent],
      providers: [
        { provide: MatDialogRef, useValue: jasmine.createSpyObj('MatDialogRef', ['close']) },
        { provide: MAT_DIALOG_DATA, useValue: {} }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ConfirmDeletionModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should close with true when confirmed', () => {
    component.onConfirm();

    expect(component.dialogRef.close).toHaveBeenCalledWith(true);
  });

  it('should close with false when cancelled', () => {
    component.onCancel();

    expect(component.dialogRef.close).toHaveBeenCalledWith(false);
  });
});
