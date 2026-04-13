import { Component, OnInit, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';

@Component({
    selector: 'app-confirm-deletion-modal',
    templateUrl: './confirm-deletion-modal.component.html',
    styleUrls: ['./confirm-deletion-modal.component.scss'],
    imports: [
        MatButtonModule,
        MatDialogModule
    ]
})
export class ConfirmDeletionModalComponent  implements OnInit {

  constructor(
    public dialogRef: MatDialogRef<ConfirmDeletionModalComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { message: string }
  ) { }

  onConfirm(): void {
    this.dialogRef.close(true);
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }

  ngOnInit() {
    
  }


}

