import { AreaPlugin } from "rete-area-plugin";
import { daavBlock, NodeBlock } from "../node-block";
import { TransformBlock } from "../transform/transform-block";
import { AreaExtra, Schemes } from "src/app/core/workflow-editor";
import { Node } from "src/app/models/interfaces/node";
import { StatusNode } from "src/app/enums/status-node";
import { ClassicPreset } from "rete";
import { FlatObjectSocket} from "src/app/core/sockets/sockets";
import { WorkflowNodeEditor } from "src/app/core/workflow-node-editor";
import { DataFilterControl } from "src/app/components/widgets/data-filter-widget/data-filter-widget.component";
import { Connection } from "rete/_types/presets/classic";
import { DataMapperUtils } from "src/app/models/data-mapper-types";


@daavBlock("transform")
export class FilterTransform extends TransformBlock {
    override getRevision(): string {
        throw new Error("Method not implemented.");
    }
    override width = 350;
    override height = 192;
    dataFilterControl: DataFilterControl;
    dataSource: string;

    constructor(label: string, area: AreaPlugin<Schemes, AreaExtra>, node? : Node){
        super(label, area, node);
        console.log("here node ", node)
        if (!node){
            // to configure the input 
            this.updateStatus(StatusNode.Incomplete);
            this.addInput(
            "datasource",
            new ClassicPreset.Input(new FlatObjectSocket(), "DataSource")
            );

        };
        
        const contextPipe = context => {
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

        if(node){
            console.log(node.data?.datasets)
            this.dataFilterControl = new DataFilterControl(node.data?.datasets, this.onFilterClose.bind(this))
            if(node.data?.filterRules){
                this.dataFilterControl.query = node.data.filterRules;
            }
            if(node.data?.dataSource){
                this.dataSource = node.data?.dataSource
            }
        }else {
            this.dataFilterControl = new DataFilterControl([] , this.onFilterClose.bind(this))
        }

        this.addControl("datafilter", this.dataFilterControl);
    }

    onFilterClose(){
        const hasRules = this.dataFilterControl.query &&
                         this.dataFilterControl.query.rules &&
                         this.dataFilterControl.query.rules.length > 0;
        if(hasRules){
            console.log("rules: ", this.dataFilterControl.query)
            this.updateStatus(StatusNode.Complete);
        }else {
            this.updateStatus(StatusNode.Incomplete);
        }
    }

    private onConnectionChange(connection: Connection<NodeBlock, NodeBlock>, type: 'connectioncreated'|'connectionremoved' ){
        const worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
        if ( connection.targetInput === "datasource" ){
            if ( type === 'connectioncreated' ){
                const sourceNode = worflowEditor.getNode(connection.source);
                if ( sourceNode ){
                    const sourceOutputSocket = sourceNode.outputs[connection.sourceOutput].socket;
                    this.addOutput(
                        "out",
                        new ClassicPreset.Output(sourceOutputSocket, "Out")
                    );
                }
            }
            
            else {
                const connectionOutput = worflowEditor.getConnections().find(conn => conn.source === this.id && conn.sourceOutput === "out");
                if ( connectionOutput ){
                    worflowEditor.removeConnection(connectionOutput.id)
                }
                this.removeOutput("out");
            }
        }
        this.buildDataset(type);
    }

    private buildDataset(type: 'connectioncreated'|'connectionremoved'|'nodeDataOutputUpdated'){
        const worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
        const connection = worflowEditor.getConnections().find(connection => connection.target === this.id)
        
        this.dataFilterControl.datasets = [];

        if (connection) {
            const sourceNode = worflowEditor.getNode(connection.source)
            if ( sourceNode ) {
                const nodeData = sourceNode.dataOutput.get(connection.sourceOutput);
                this.dataSource = connection.targetInput
                this.dataFilterControl.datasets = [ DataMapperUtils.nodeDataToMapper(nodeData, this.dataSource) ];
            }
        }
        
        if ( type === 'connectionremoved' ){
            this.dataFilterControl.datasets = [];
            console.log("connexion removed")
            this.resetQuery();

        }
        this.area.update('node', this.id);
    }

    private resetQuery(){
        if(this.dataFilterControl){
            this.dataFilterControl.query = {
                condition: 'and',
                rules: []
            }
        }
    }

    override data(){
        const data ={ 
            datasets : this.dataFilterControl.datasets,
            filterRules: this.dataFilterControl.query,
            dataSource: this.dataSource
        };
        return {...super.data(),...data};
    }
}