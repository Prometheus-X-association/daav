import { Component, inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef , MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';

@Component({
    selector: 'app-confirm-deletion-modal',
    templateUrl: './confirm-deletion-modal.component.html',
    imports: [
        MatButtonModule,
        MatDialogModule
    ]
})
export class ConfirmDeletionModalComponent {
  dialogRef = inject<MatDialogRef<ConfirmDeletionModalComponent>>(MatDialogRef);
  data = inject<{ message: string }>(MAT_DIALOG_DATA);

  onConfirm(): void {
    this.dialogRef.close(true);
  }

  onCancel(): void {
    this.dialogRef.close(false);
    }

}

