
import {
  Component,
  Input,
  HostBinding,
  ChangeDetectorRef,
  OnChanges,
  inject
} from "@angular/core";
import { ClassicPreset } from "rete";
import { KeyValue, KeyValuePipe } from "@angular/common";
import { RefDirective } from "rete-angular-plugin/21";

@Component({
    selector: 'app-transform-node',
    templateUrl: 'nodes.component.html',
    styleUrls: ['nodes.component.scss'],
    host: {
        "data-testid": "node",
        "class": " node transform-node"
    },
    imports: [RefDirective, KeyValuePipe]
})
export class TransformNodeComponent implements OnChanges {
  private readonly cdr = inject(ChangeDetectorRef);

  @Input() data!: ClassicPreset.Node;
  @Input() emit!: (data: any) => void;
  @Input() rendered!: () => void;
  seed = 0;

  cdrLoc = this.cdr;
  @HostBinding("class.selected") get selected() {
    return this.data.selected;
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
