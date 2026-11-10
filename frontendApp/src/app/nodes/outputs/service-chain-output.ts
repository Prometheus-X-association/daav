import { AreaPlugin } from "rete-area-plugin";
import { daavBlock } from "../node-block";
import { OutputDataBlock } from "../output/output-data-block";
import { AreaExtra, Schemes } from "src/app/core/workflow-editor";
import { Node } from 'src/app/models/interfaces/node';
import { StatusNode } from "src/app/enums/status-node";
import { ClassicPreset } from "rete";
import { AllSocket } from "src/app/core/sockets/sockets";
import { WorkflowNodeEditor } from "src/app/core/workflow-node-editor";
import { DatasetPTX } from "src/app/models/dataset-ptx";
import { SelectControl } from "src/app/components/widgets/select-widget/select-widget.component";
import { MatSelectChange } from "@angular/material/select";

@daavBlock("output")
export class ServiceChainOutput extends OutputDataBlock{
  override width = 350;
  private readonly node: Node;
  selectControlDataset: SelectControl;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ){
    super(label, area, node);
    this.worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
    this.filterInputType = [];
    this.filterInputType.push(DatasetPTX);
    this.node = node;


    if(!node) {
      this.status = StatusNode.Incomplete;
      this.addInput(
        'in',
        new ClassicPreset.Input(new AllSocket(), "In")
      )
    }

    this.area.update("node", this.id);
  }

  override dataSourceChange(event: MatSelectChange) {
    console.log('database source change', event);
    if (event.value) {
      this.updateStatus(StatusNode.Complete);
    } else {
      this.updateStatus(StatusNode.Incomplete);
    }
    this.area.update('node', this.id);
  }
}
