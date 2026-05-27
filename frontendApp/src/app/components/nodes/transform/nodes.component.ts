import { NodeComponent } from "rete-angular-plugin/19";

import {
  Component,
  Input,
  HostBinding,
  ChangeDetectorRef,
  OnChanges
} from "@angular/core";
import { ClassicPreset } from "rete";
import { KeyValue } from "@angular/common";

@Component({
    selector: 'app-transform-node',
    templateUrl: 'nodes.component.html',
    styleUrls: ['nodes.component.scss'],
    // eslint-disable-next-line @angular-eslint/no-host-metadata-property
    host: {
        "data-testid": "node",
        "class": " node transform-node"
    },
    standalone: false
})
export class TransformNodeComponent implements OnChanges {
  @Input() data!: ClassicPreset.Node;
  @Input() emit!: (data: any) => void;
  @Input() rendered!: () => void;
  seed = 0;

  cdrLoc = this.cdr;
  @HostBinding("class.selected") get selected() {
    return this.data.selected;
  }

  constructor(private cdr: ChangeDetectorRef) {
    //this.cdr.detach();
  }

  ngOnChanges(): void {
    this.cdr.detectChanges();
    requestAnimationFrame(() => this.rendered());
    this.seed++; // force render sockets
  }

  sortByIndex<
    N extends object,
    T extends KeyValue<string, N & { index?: number }>
  >(a: T, b: T) {
    const ai = a.value.index || 0;
    const bi = b.value.index || 0;

    return ai - bi;
  }
}
