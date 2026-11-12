import { NodeBlock } from "../node-block";
import { TransformNodeComponent } from "src/app/components/nodes/transform/nodes.component";
import { CheckboxControl, CheckboxControlI } from 'src/app/components/widgets/checkbox-widget/checkbox-widget.component';

import { Node } from "src/app/models/interfaces/node";
import { AreaPlugin } from "rete-area-plugin";
import { Schemes, AreaExtra } from "src/app/core/workflow-editor";
import { MatSelectChange } from "@angular/material/select";


export class TransformBlock extends NodeBlock{

    parquetCheckbox: CheckboxControl;
    constructor(label:string,area : AreaPlugin<Schemes, AreaExtra>,node?:Node){
          super(label,area,node)
          this.addParquetSave(node);
    }

    addParquetSave(node: Node){
        console.log('addParquetSave');
        let parquetSave: CheckboxControlI;
        if(node?.data?.parquetSave) {
          parquetSave = node.data?.parquetSave;
        }
        else {
          parquetSave = {
            value: false,
            label: 'Parquet',
          }
        }
        this.parquetCheckbox = new CheckboxControl(parquetSave,this.parquetSaveChange.bind(this));
        this.addControl('parquet', this.parquetCheckbox);
        void this.area.update('node', this.parquetCheckbox.id);
      }

    parquetSaveChange(event: MatSelectChange){
        console.log('parquet save change',event);
    }

    override data() {
        const data = {
          parquetSave: this.parquetCheckbox,
        };
        return { ...super.data(), ...data };
    }

    getRevision(){
        return "123";
    }

    override getNodeComponent():any {
        return TransformNodeComponent;
    }
}
