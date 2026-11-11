import { Node } from "src/app/models/interfaces/node";
import { InputDataBlock } from "../input/input-data-block";
import { AreaPlugin } from "rete-area-plugin";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";

export class DataLrsBlock extends InputDataBlock{

    constructor(label:string,area : AreaPlugin<Schemes, AreaExtra>,node?:Node){
        super(label,area,node)
    }


    override execute(){
        // Intentionally empty: this block cannot be executed on its own yet.
    }

}
