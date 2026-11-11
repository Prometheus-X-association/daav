import { Component, Input } from "@angular/core";
import { ClassicPreset } from "rete";

@Component({
    selector: 'app-custom-connections',
    // templateUrl: './connections.component.html',
    styleUrls: ['./connections.component.scss'],
    template: `
    <svg data-testid="connection">
      <path [attr.d]="path" />
    </svg>
  `,
})
export class CustomConnectionComponent {
  @Input() data!: ClassicPreset.Connection<
    ClassicPreset.Node,
    ClassicPreset.Node
  >;
  @Input() start: any;
  @Input() end: any;
  @Input() path: string;
}
