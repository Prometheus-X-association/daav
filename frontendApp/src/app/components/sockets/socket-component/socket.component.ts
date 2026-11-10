import { ChangeDetectorRef, Component, HostBinding, Input, OnChanges, inject } from '@angular/core';

@Component({
    selector: 'app-socket-component',
    template: '',
    styleUrls: ['./socket.component.scss'],
})
export class SocketComponent  implements OnChanges {
  private readonly cdr = inject(ChangeDetectorRef);

  @Input() data!: any;
  @Input() rendered!: any;

  @HostBinding("title") get title() {
    return this.data.name;
  }

  constructor() {
    this.cdr.detach();
  }

  ngOnChanges(): void {
    this.cdr.detectChanges();
    requestAnimationFrame(() => this.rendered());
  }

}
