// import { Component, OnInit } from '@angular/core';

// @Component({
//   selector: 'app-connections',
//   templateUrl: './connections.component.html',
//   styleUrls: ['./connections.component.scss'],
// })
// export class ConnectionsComponent  implements OnInit {

//   constructor() { }

//   ngOnInit() {}

// }


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
    standalone: false
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
