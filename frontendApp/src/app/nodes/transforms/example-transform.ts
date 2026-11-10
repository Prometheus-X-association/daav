import { ClassicPreset } from "rete";
import { AreaPlugin } from "rete-area-plugin";
import { SimpleFieldSocket, FlatObjectSocket, DeepObjectSocket } from "src/app/core/sockets/sockets";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { StatusNode } from "src/app/enums/status-node";
import { Node } from "src/app/models/interfaces/node";
import { TransformBlock } from "../transform/transform-block";



//@daavBlock('transform')
export class ExampleTransform extends TransformBlock {
  override getRevision(): string {
    throw new Error("Method not implemented.");
  }
  override width = 350;
  override height = 192;
  constructor(label : string,area : AreaPlugin<Schemes, AreaExtra>,node? : Node){
    super(label,area,node);
    if (!node){
      this.status = StatusNode.Incomplete;
      this.addInput(
        "colonne",
        new ClassicPreset.Input(new SimpleFieldSocket(), "Colonne")
      );
      this.addInput(
        "consequent",
        new ClassicPreset.Input(new FlatObjectSocket(), "Full")
      );
      this.addOutput(
        "alternate",
        new ClassicPreset.Output(new FlatObjectSocket(), "Full")
      );
      this.addOutput(
        "new",
        new ClassicPreset.Output(new DeepObjectSocket(), "Lrs")
      );
    }
    this.updateStatus(StatusNode.Valid,"Good to launch");
  }

}
