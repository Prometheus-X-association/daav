import { ClassicPreset } from "rete";
import { AreaPlugin } from "rete-area-plugin";
import { FlatObjectSocket, DeepObjectSocket } from "src/app/core/sockets/sockets";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { StatusNode } from "src/app/enums/status-node";
import { daavBlock, NodeBlock } from "../node-block";
import { Node } from "src/app/models/interfaces/node";
import { TransformBlock } from "../transform/transform-block";
import { WorkflowNodeEditor } from "src/app/core/workflow-node-editor";
import { Connection } from "rete/_types/presets/classic";



@daavBlock('transform')
export class FlattenTransform extends TransformBlock {
  worflowEditor: WorkflowNodeEditor<Schemes>;
  override getRevision(): string {
    throw new Error("Method not implemented.");
  }
  override width = 350;
  override height = 192;
  constructor(label : string,area : AreaPlugin<Schemes, AreaExtra>,node? : Node){
    super(label,area,node);
    this.worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
    if (!node){
      this.status = StatusNode.Incomplete;
      this.addInput(
        "datasource",
        new ClassicPreset.Input(new DeepObjectSocket(), "DataSource")
      );
      this.addOutput(
        "out",
        new ClassicPreset.Output(new FlatObjectSocket, "Out")
      );
    }

    //handle event from rete area connection disconnection output update
    const contextPipe = context => {
      //when preventNodeEvent is set disable callback on new connection (useful to restore workflow)
      if (context.type === 'clear') {
        this.preventNodeEvent = true;
      }
      if (context.type === 'cleared' || context.type === 'clearcancelled') {
        this.preventNodeEvent = false;
      }
      if (!this.preventNodeEvent){
        if (context.type === 'connectioncreated' || context.type === 'connectionremoved') {
          const { target } = context.data;
          if (target === this.id) {
            console.log('Connection changed for node:', context);
            this.onConnectionChange(context.data,context.type);
          }
        }
      }
      if (context.type === 'noderemoved') {
        if (context.data.id === this.id) {
          area.signal.pipes.splice(area.signal.pipes.indexOf(contextPipe), 1);
        }
      }
      return context;
    };
    area.addPipe(contextPipe);
  }

    /**
     * Create or remove programmatically input each time an input is connected or disconnected
     * @param connection
     * @param type
     */
    private onConnectionChange(connection : Connection<NodeBlock, NodeBlock>,type : 'connectioncreated'|'connectionremoved') {
      console.log('Connection changed for node:', this.id);
      if (connection.targetInput === "datasource" ){
        if (type === 'connectioncreated'){
          this.updateStatus(StatusNode.Complete);
          this.execute();
        } else {
          this.updateStatus(StatusNode.Incomplete);
          this.dataOutput.set("out", null);
          this.worflowEditor.core.nodeEditor.emit({
            type: "nodeDataOutputUpdated",
            data: {
                nodeId: this.id,
                outputKey: "out",
            }
          });
        }

      }
    }

}
