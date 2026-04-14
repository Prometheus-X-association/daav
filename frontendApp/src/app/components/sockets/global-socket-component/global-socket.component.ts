import { ChangeDetectorRef, Component, HostBinding, Input, OnChanges} from '@angular/core';

@Component({
    selector: 'app-global-socket-component',
    template: '',
    styleUrls: ['./global-socket.component.scss'],
    standalone: false
})
export class GlobalSocketComponent  implements OnChanges {

  @Input() data!: any;
  @Input() rendered!: any;

  @HostBinding("title") get title() {
    return this.data.name;
  }

  constructor(private cdr: ChangeDetectorRef) {
    this.cdr.detach();
  }

  ngOnChanges(): void {
    this.cdr.detectChanges();
    requestAnimationFrame(() => this.rendered());
  }

}
