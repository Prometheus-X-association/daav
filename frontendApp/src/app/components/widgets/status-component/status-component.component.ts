import { NgClass, NgStyle } from '@angular/common';
import { ChangeDetectorRef, Component, Input } from '@angular/core';
import { OverlayEventDetail } from '@ionic/core';
import { ClassicPreset } from 'rete';
import { StatusNode } from 'src/app/enums/status-node';

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
    standalone: false
})
export class StatusComponentComponent {
  @Input() data: StatusControl;
  enumStatus = StatusNode;

  isModalOpen = false;
  cdr: ChangeDetectorRef;


  constructor(cdr: ChangeDetectorRef) {
    this.cdr = cdr;
  }

  setOpen(isOpen: boolean) {
    this.isModalOpen = isOpen;
  }

  onWillDismiss(event: Event) {
    this.isModalOpen = false;
    const ev = event as CustomEvent<OverlayEventDetail<string>>;
  }
}
