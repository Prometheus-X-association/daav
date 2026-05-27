import { ClassicPreset } from "rete";
import { StatusNode } from "../enums/status-node";
import { Node } from "../models/interfaces/node";
import { StatusControl } from "../components/widgets/status-component/status-component.component";
import { AreaPlugin } from "rete-area-plugin";
import { AreaExtra, Schemes, WorkflowEditor } from "../core/workflow-editor";
import { NodeComponent } from "rete-angular-plugin/19";
import { NodeLoaderControl } from '../components/widgets/node-loader-widget/node-loader-widget.component';
import { NodeData } from '../models/node-data';
import { DatasetSchema } from "../models/dataset-schema";
import { ButtonControl } from "../components/widgets/button-widget/button-widget.component";
import { WorkflowNodeEditor } from "../core/workflow-node-editor";

export const registeredBlock = new Map<string, {class : object, type}>();
export function daavBlock(type=null) {
     return function(target) {
      registeredBlock.set(target.name,{class : target, type});
     };
}

export abstract class NodeBlock<G=DatasetSchema,T = NodeData<G>> extends ClassicPreset.Node  {
    status : StatusNode;
    statusMessage : string;
    errorStacktrace : string[];
    rebuildLocally = false;
    preventNodeEvent = false;
    dataOutput : Map<OutputId,T>;
    private statusControl: StatusControl;
    width = 250;
    height = 120;
    nodeLoader: NodeLoaderControl;
    playButtonControl: ButtonControl;
    /**
     *
     * @param label Title label of a node
     * @param area Rete js area to update widget content
     * @param node Node interface to instantiate a node from import source
     */
    constructor(label : string,public area : AreaPlugin<Schemes, AreaExtra>,node? : Node){
      super(label);
      this.dataOutput = new Map();
      this.status= StatusNode.Incomplete;
      if (node){
        this.status = node.data?.status;
        this.statusMessage = node.data?.statusMessage;
        this.errorStacktrace = node.data?.errorStacktrace;
        if (node.data?.dataOutput){
          this.dataOutput = new Map(Object.entries(node.data?.dataOutput));
        }
      }
      this.statusControl = new StatusControl(this.status,this.statusMessage,this.errorStacktrace);
      this.addControl("status",this.statusControl);
      area.update("control", this.statusControl.id);
      this.playButtonControl = new ButtonControl(()=>{
        this.execute();
      },null,"play_arrow","playButton");
      this.playButtonControl.disabled = (this.status === StatusNode.Incomplete);
      this.addControl("play",this.playButtonControl);
      area.update("control", this.playButtonControl.id);
      this.nodeLoader = new NodeLoaderControl();
      this.addControl("loader",this.nodeLoader);
    }
    /**
     * Internal data for the node this is serialization for inport export node information
     * @returns {}
     */
    data(){
      return {status :this.status,
        statusMessage : this.statusMessage,
        errorStacktrace : this.errorStacktrace,
        dataOutput : Object.fromEntries(this.dataOutput)
      };
    }

    /**
     * Return the component render of the node override to select a custom renderer for node
     * @returns
     */
    getNodeComponent(){
      return NodeComponent;
    }

    /**
     * Update node status
     * @param status Actual status of the node coloryzed indicator
     * @param statusMessage status message inside hover tootip on the status indicator
     * @param errorStacktrace modal for error status when click on indicator
     */
    updateStatus(status : StatusNode,statusMessage?:string,errorStacktrace? : string[]){
      this.status = status;
      this.statusMessage = statusMessage;
      this.errorStacktrace = errorStacktrace;
      this.statusControl.status=status;
      this.statusControl.statusMessage=statusMessage;
      this.statusControl.errorStacktrace=errorStacktrace;
      this.playButtonControl.disabled = (status === StatusNode.Incomplete);
      this.area.update("node",this.id);
      this.area.update("control", this.statusControl.id);
    }

    /**
     * Activate a loader who cover the node
     * @param show
     */
    showLoader(show : boolean){
      this.nodeLoader.loading = show;
      this.area.update("control", this.nodeLoader.id);
    }

    execute(){
      (this.area.parent as WorkflowNodeEditor<Schemes>).core.executeNodeJson(this.id)
    }

    /**
     * Process node response from backend
     * Can be overridden by child classes for custom response handling
     * @param response Response data from backend
     */
    processNodeResponse(response: any) {
        if (response?.data) {
            // Update node data if needed
            Object.assign(this.data(), response.data);

            // Update area to reflect changes
            this.area.update("node", this.id);
        }
    }

    /**
     * revision code custom node have to reflect all internal data and parameter in this code to detect change inside configuration
     */
    abstract getRevision():string
  }

  export type OutputId = string;
