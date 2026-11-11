import { AreaPlugin } from "rete-area-plugin";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { Node } from "../../models/interfaces/node";
import { InputDataBlock } from "../input/input-data-block";

export class DataApiBlock extends InputDataBlock{

    constructor(label:string,area : AreaPlugin<Schemes, AreaExtra>,node?:Node){
        super(label,area,node)
    }


    override execute(){
        // Intentionally empty: this block cannot be executed on its own yet.
    }
}
