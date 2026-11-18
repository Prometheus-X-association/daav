import { AreaPlugin } from "rete-area-plugin";
import { OutputDataBlock } from "../output/output-data-block";
import { AreaExtra, Schemes } from "src/app/core/workflow-editor";
import { StatusNode } from "src/app/enums/status-node";
import { ClassicPreset } from "rete";
import { FlatObjectSocket, SimpleFieldSocket } from "src/app/core/sockets/sockets";
import { Node } from "src/app/models/interfaces/node";

//@daavBlock('output')
export class ExampleOutput extends OutputDataBlock{
  override getRevision(): string {
    throw new Error("Method not implemented.");
  }
  override width = 350;
  override height = 156;
  constructor(label : string,area : AreaPlugin<Schemes, AreaExtra>,node? : Node){
    super(label,area,node);
    if (!node){
      this.status = StatusNode.Incomplete;
      this.addInput(
        "oneColonne",
        new ClassicPreset.Input(new SimpleFieldSocket(), "Colonne")
      );
      this.addInput(
        "flatObject",
        new ClassicPreset.Input(new FlatObjectSocket(), "Full")
      );
    }
  }
}
