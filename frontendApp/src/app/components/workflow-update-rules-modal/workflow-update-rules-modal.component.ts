import { Component, inject, signal } from '@angular/core';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-workflow-update-rules-modal',
    imports: [
        MatDialogModule,
        MatCheckboxModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        FormsModule,
        CommonModule
    ],
    templateUrl: './workflow-update-rules-modal.component.html',
    styleUrls: ['./workflow-update-rules-modal.component.scss']
})
export class WorkflowUpdateRulesModalComponent {
  private dialogRef = inject(MatDialogRef<WorkflowUpdateRulesModalComponent>);

  automatic = false;
  updateText = '';

  close() {
    this.dialogRef.close(null);
  }

  confirm() {
    this.dialogRef.close({
      automatic: this.automatic,
      updateText: this.updateText
    });
  }
}
