import { ChangeDetectorRef, Component, HostBinding, Input, OnChanges} from '@angular/core';

@Component({
  selector: 'app-flat-socket-component',
  template:'',
  styleUrls: ['./flat-socket.component.scss'],
})
export class FlatSocketComponent  implements OnChanges {

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
