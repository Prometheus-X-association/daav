import { Component, inject } from '@angular/core';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';


@Component({
    selector: 'app-workflow-update-rules-modal',
    imports: [
    MatDialogModule,
    MatCheckboxModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    FormsModule
],
    templateUrl: './workflow-update-rules-modal.component.html',
})
export class WorkflowUpdateRulesModalComponent {
  private readonly dialogRef = inject(MatDialogRef<WorkflowUpdateRulesModalComponent>);

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
