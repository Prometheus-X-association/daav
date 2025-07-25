import { ClassicPreset } from "rete";
import { FlatObjectSocket, SimpleFieldSocket } from "src/app/core/sockets/sockets";
import { Node } from "src/app/models/interfaces/node";
import { StatusNode } from "src/app/enums/status-node";
import { AreaExtra, Schemes } from "src/app/core/workflow-editor";
import { AreaPlugin } from "rete-area-plugin";
import { InputDataBlock } from "../input/input-data-block";
import { daavBlock } from "../node-block";
// import { NodeComponent } from "src/app/components/nodes/nodes.component";

//@daavBlock('input')
export class ExampleInput extends InputDataBlock {
  override getRevision(): string {
    throw new Error("Method not implemented.");
  }
  override width = 350;
  override height = 156;
  constructor(label : string,area : AreaPlugin<Schemes, AreaExtra>,node? : Node){
    super(label,area,node);
    if (!node){
      this.status = StatusNode.Incomplete;
      this.addOutput(
        "consequent",
        new ClassicPreset.Output(new SimpleFieldSocket(), "Colonne")
      );
      this.addOutput(
        "alternate",
        new ClassicPreset.Output(new FlatObjectSocket(), "Full")
      );
      this.addOutput(
        "solo",
        new ClassicPreset.Output(new FlatObjectSocket(), "Solo")
      );
    }
  }
}
