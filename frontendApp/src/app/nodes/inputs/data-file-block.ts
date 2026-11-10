import { ClassicPreset } from 'rete';
import {
  DeepObjectSocket,
  FlatObjectSocket,
} from 'src/app/core/sockets/sockets';
import { Node } from 'src/app/models/interfaces/node';
import { StatusNode } from 'src/app/enums/status-node';
import { AreaExtra, Schemes } from 'src/app/core/workflow-editor';
import { AreaPlugin } from 'rete-area-plugin';
import { InputDataBlock } from '../input/input-data-block';
import { daavBlock } from '../node-block';
import { MatSelectChange } from '@angular/material/select';
import { DatasetFile } from 'src/app/models/dataset-file';
import { PandasSchema, PandasSchemaUtils } from 'src/app/models/dataset-schema';
import { NodeDataPandasDf } from 'src/app/models/node-data';

@daavBlock('input')
export class DataFileBlock extends InputDataBlock<PandasSchema, NodeDataPandasDf> {
  override getRevision(): string {
    throw new Error('Method not implemented.');
  }
  override width = 350;
  override height = 156;
  pagination = {
    perPage: 5,
    page: 1,
  };
  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.filterInputType = [];
    this.filterInputType.push(DatasetFile);
  }

  override async dataSourceChange(event: MatSelectChange) {
    console.log('data source change', event);
    if ( !await this.confirmChangeSource(event)) {
        return;
    }
    this.cleanOutput();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find((dataset) => dataset.id === event.value) as DatasetFile;
      this.showLoader(true);
      this.datasetService
        .getDfContentDataset(dataset, this.pagination)
        .subscribe({
          next: (data) => {
            console.log(data);
            if (data) {
              this.createOutput(data);
              this.status = StatusNode.Complete;
            }
            this.showLoader(false);
          },
          error: (err) => {
            this.showLoader(false);
            console.error(err);
          },
        });
    }
  }

    createOutput(
      data: NodeDataPandasDf
    ) {
      this.addOutput(
        'out',
        new ClassicPreset.Output(PandasSchemaUtils.isDeepObjectSchema(data.nodeSchema)?new DeepObjectSocket(): new FlatObjectSocket(), `${data.name} -> Out`)
      );
      this.dataOutput.set('out', data);
      this.updateStatus(StatusNode.Complete);
      this.area.update('node', this.id);
    }

  cleanOutput() {
    if (this.outputs['out']) {
      const connection = this.worflowEditor
        .getConnections()
        .find((conn) => conn.source === this.id && conn.sourceOutput === 'out');
      if (connection) {
        this.worflowEditor.removeConnection(connection.id);
      }
      this.removeOutput('out');
      this.dataOutput.delete('out');
    }
    this.updateStatus(StatusNode.Incomplete);
    this.area.update('node', this.id);
  }
}
