import { ChangeDetectorRef, Component, Input, inject } from '@angular/core';
import { OverlayEventDetail } from '@ionic/core';
import { ClassicPreset } from 'rete';
import { StatusNode } from 'src/app/enums/status-node';
import { MatTooltip } from '@angular/material/tooltip';
import { NgClass } from '@angular/common';
import { IonicModule } from '@ionic/angular';

export class StatusControl extends ClassicPreset.Control {
  constructor(
    public status: StatusNode,
    public statusMessage: string,
    public errorStacktrace: string[]
  ) {
    super();
  }
}

@Component({
    selector: 'app-status-component',
    templateUrl: './status-component.component.html',
    styleUrls: ['./status-component.component.scss'],
    imports: [MatTooltip, NgClass, IonicModule]
})
export class StatusComponentComponent {
  @Input() data: StatusControl;
  enumStatus = StatusNode;

  isModalOpen = false;
  cdr = inject(ChangeDetectorRef);

  /** Text alternative for the status color */
  statusLabel(): string {
    const label = `Status: ${StatusNode[this.data.status]}`;
    return this.data.statusMessage ? `${label}. ${this.data.statusMessage}` : label;
  }

  setOpen(isOpen: boolean) {
    this.isModalOpen = isOpen;
  }

  onWillDismiss(event: Event) {
    this.isModalOpen = false;
    const ev = event as CustomEvent<OverlayEventDetail<string>>;
  }
}
