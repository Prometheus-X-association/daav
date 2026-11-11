import { ClassicPreset } from "rete";
import { AreaPlugin } from "rete-area-plugin";
import { AllSocket} from "src/app/core/sockets/sockets";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { StatusNode } from "src/app/enums/status-node";
import { TransformBlock } from "../transform/transform-block";
import { Node } from "src/app/models/interfaces/node";
import { daavBlock, NodeBlock } from "../node-block";
import { Connection } from "rete/_types/presets/classic";
import { WorkflowNodeEditor } from "src/app/core/workflow-node-editor";
import { DataMapperControl } from "src/app/components/widgets/data-mapper-widget/data-mapper-widget.component";
import { DataMapperUtils } from "src/app/models/data-mapper-types";

@daavBlock('transform')
export class MergeTransform extends TransformBlock {
  dataMapperControl: DataMapperControl;
  override getRevision(): string {
    throw new Error("Method not implemented.");
  }
  override width = 350;
  override height = 192;
  constructor(label : string,area : AreaPlugin<Schemes, AreaExtra>,node? : Node){
    super(label,area,node);
    if (!node){
      this.updateStatus(StatusNode.Incomplete);
      this.addInput(
        "datasource",
        new ClassicPreset.Input(new AllSocket(), "DataSource")
      );
    }
    if (node){
      //import data mapping when restore
      this.dataMapperControl = new DataMapperControl(node.data.dataMapping,node.data?.datasets,this.onMapperClose.bind(this));
      console.log("data.dataset", node.data)
    } else {
      this.dataMapperControl = new DataMapperControl([],[],this.onMapperClose.bind(this));
    }

    this.addControl("dataMapper",this.dataMapperControl);
    area.update("control", this.dataMapperControl.id);
    //save the callback to remove from area pipe from signal arrays because no method to remove
    const contextPipe = context => {
      //when clear in progress disable event
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
      if (context.type === 'nodeDataOutputUpdated') {
        console.log('Node data output updated:', context);
        const worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
        const incomingConnections = worflowEditor.getConnections().filter(connection => connection.target === this.id && connection.source === context.data.nodeId && connection.sourceOutput === context.data.outputKey);
        if (incomingConnections.length > 0){
          console.log('Incoming connections:', incomingConnections);
          this.buildDataset(context.type);
        }
      }
      return context;
    };
    area.addPipe(contextPipe);
  }


  override data(){
    const data ={dataMapping : this.dataMapperControl.mappings , datasets : this.dataMapperControl.datasets};
    return {...super.data(),...data};
  }

  /**
   * Create or remove programmatically input each time an input is connected or disconnected
   * @param connection
   * @param type
   */
  private onConnectionChange(connection : Connection<NodeBlock, NodeBlock>,type : 'connectioncreated'|'connectionremoved') {
    console.log('Connection changed for node:', this.id);
    // get node source from area
    const worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
    if (connection.targetInput === "datasource" ){
      if (type === 'connectioncreated'){
        const newInputKey = "datasource_1";
        const sourceNode = worflowEditor.getNode(connection.source);
        if (sourceNode){
          const sourceOutputSocket = sourceNode.outputs[connection.sourceOutput].socket;
          this.addInput(
            newInputKey,
            new ClassicPreset.Input(sourceOutputSocket, "DataSource 1")
          );
          this.addOutput(
            "out",
            new ClassicPreset.Output(sourceOutputSocket, "Out")
          );
        }
      } else {
        //delete all other inputs with her connections they have to have the same socket as primary datasource
        Object.entries(this.inputs).forEach(([key, input]) => {
          if (key !== "datasource") {
            const connection = worflowEditor.getConnections().find(conn => conn.target === this.id && conn.targetInput === key);
            if (connection){
              worflowEditor.removeConnection(connection.id);
            }
            this.removeInput(key);
          }
          const connectionOuput = worflowEditor.getConnections().find(conn => conn.source === this.id && conn.sourceOutput === "out");
          if (connectionOuput){
            worflowEditor.removeConnection(connectionOuput.id);
          }
          this.removeOutput("out");
        });

      }

    }
    const match = connection.targetInput.match(/^datasource(_(\d+))?$/);
    //when a input like datasource_x is connected  we create a new input if increment not exist
    if (match) {
      if (type === 'connectioncreated'){
        const index = match[2] ? parseInt(match[2], 10) + 1 : 1;
        const existingKeys = Object.keys(this.inputs);
        const newInputKey = `datasource_${index}`;
        if (!existingKeys.includes(newInputKey)) {

          const sourceOutputSocket = this.inputs[connection.targetInput].socket;
          this.addInput(
            newInputKey,
            new ClassicPreset.Input(sourceOutputSocket, `DataSource ${index}`)
          );
        }
      }else {
        const index = match[2] ? parseInt(match[2], 10) : 0;
        const nextInputKey = `datasource_${index + 1}`;
        //remove +1 input if not connected when remove connection of the current input
        if (this.inputs[nextInputKey]) {
          const hasConnection = worflowEditor.getConnections().some(conn => conn.target === this.id && conn.targetInput === nextInputKey);
          if (!hasConnection) {
            this.removeInput(nextInputKey);
          }
        }
        //remove -1  input too if it's not connected
        if (index >1){
          const prevInputKey = `datasource_${index-1}`;
          if (this.inputs[prevInputKey]) {
            const hasPrevConnection = worflowEditor.getConnections().some(conn => conn.target === this.id && conn.targetInput === prevInputKey);
            if (!hasPrevConnection) {
              this.removeInput(connection.targetInput);
            }
          }
        }
      }
    }
    this.buildDataset(type);
  }

  onMapperClose(){
    if (this.dataMapperControl.mappings?.length > 0) {
      this.updateStatus(StatusNode.Complete);
    } else {
      this.updateStatus(StatusNode.Incomplete);
    }
  }

  private buildDataset(type : 'connectioncreated'|'connectionremoved'|'nodeDataOutputUpdated'){
    const worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
    const incomingConnections = worflowEditor.getConnections().filter(connection => connection.target === this.id)

    this.dataMapperControl.datasets = [];
    incomingConnections.forEach(connection => {
      const sourceNode = worflowEditor.getNode(connection.source);
      if (sourceNode){
        const nodeData = sourceNode.dataOutput.get(connection.sourceOutput);
        console.log("source Node data: ", nodeData )
        if (nodeData){
          this.dataMapperControl.datasets.push(DataMapperUtils.nodeDataToMapper(nodeData,connection.targetInput));
          console.log("datasetId:", connection)
        } else {
          this.dataMapperControl.mappings = [];
          this.updateStatus(StatusNode.Incomplete);
        }
      }
    });
    if (type === 'connectionremoved'){
      this.dataMapperControl.mappings = [];
    }
    this.area.update('node', this.id);
  }
}
