import { Node } from 'src/app/models/interfaces/node';
import { NodeBlock } from '../node-block';
import { ClassicPreset } from 'rete';
import {
  FlatObjectSocket,
  SimpleFieldSocket,
} from 'src/app/core/sockets/sockets';
import { AreaPlugin } from 'rete-area-plugin';
import { Schemes, AreaExtra } from 'src/app/core/workflow-editor';
import { InputNodeComponent } from 'src/app/components/nodes/input/nodes.component';
import { runInInjectionContext, inject, Signal } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { MatSelectChange } from '@angular/material/select';
import { Subscription, map } from 'rxjs';
import {
  SelectControl,
  selectControlI,
} from 'src/app/components/widgets/select-widget/select-widget.component';
import { WorkflowNodeEditor } from 'src/app/core/workflow-node-editor';
import { Dataset } from 'src/app/models/dataset';
import { DatasetService } from 'src/app/services/dataset.service';
import { DatasetSchema } from 'src/app/models/dataset-schema';
import { NodeData } from 'src/app/models/node-data';
import {
  CheckboxControl,
  CheckboxControlI,
} from 'src/app/components/widgets/checkbox-widget/checkbox-widget.component';
import { HttpClient } from '@angular/common/http';
import { AlertController } from '@ionic/angular';

export class InputDataBlock<
  G = DatasetSchema,
  T = NodeData<G>
> extends NodeBlock<G, T> {
  selectControl: SelectControl;
  datasetService: DatasetService;
  worflowEditor: WorkflowNodeEditor<Schemes>;
  selectDataSourceSub: Subscription;
  parquetCheckbox: CheckboxControl;
  filterInputType: any[];
  http: HttpClient;
  override width = 350;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
    //retrieve dataset service from injector
    this.datasetService = this.worflowEditor.injector.get(DatasetService);
    this.http = this.worflowEditor.injector.get(HttpClient);
    this.addParquetSave(node);
    this.addSourceSelect(node);
  }

  addParquetSave(node: Node) {
    console.log('addParquetSave');
    let parquetSave: CheckboxControlI;
    if (node?.data?.parquetSave) {
      parquetSave = node.data?.parquetSave;
    } else {
      parquetSave = {
        value: false,
        label: 'Parquet',
      };
    }
    this.parquetCheckbox = new CheckboxControl(
      parquetSave,
      this.parquetSaveChange.bind(this)
    );
    this.addControl('parquet', this.parquetCheckbox);
    this.area.update('node', this.parquetCheckbox.id);
  }

  parquetSaveChange(event: MatSelectChange) {
    console.log('parquet save change', event);
  }

  override getNodeComponent(): any {
    return InputNodeComponent;
  }

  /**
   * Adds a source select control to the given node.
   *
   * This function initializes a select control for the node's data source. If the node already has a
   * `selectDataSource` property, it uses that; otherwise, it creates a new select control with default values.
   * The select control is then added to the node's controls and the area is updated.
   *
   * Additionally, the function subscribes to the dataset service to update the select control's list of options
   * whenever the dataset signal changes. If the current value of the select control is not found in the updated
   * list, it resets the value to null.
   *
   * @param {Node} node - The node to which the source select control will be added.
   */
  private addSourceSelect(node: Node) {
    let selectDataSource: selectControlI;
    if (node?.data?.selectDataSource) {
      //if node is given it's an import and we report content from json
      selectDataSource = node.data?.selectDataSource;
    } else {
      selectDataSource = {
        value: null,
        list: [],
        none: true,
        label: 'Dataset',
      };
    }
    this.selectControl = new SelectControl(
      selectDataSource,
      this.dataSourceChange.bind(this)
    );
    this.addControl('dataSource', this.selectControl);
    this.area.update('control', this.selectControl.id);
    //update list from service on dataset signal
    // this is obscur toObservable have problem context and need to run in runInInjectionContext
    const result = runInInjectionContext(this.worflowEditor.injector, () => {
      const service = inject(DatasetService);
      this.selectDataSourceSub = toObservable(service.datasets)
        .pipe(
          map((params) => {
            const list = [];
            let idInside = false;
            if (this.filterInputType) {
              params = params.filter((dataset) =>
                this.filterInputType.some((type) => dataset instanceof type)
              );
            }
            params.forEach((dataset: Dataset) => {
              if (this.selectControl?.value === dataset.id) {
                idInside = true;
              }
              list.push({ label: dataset.name, value: dataset.id });
            });
            return { list, idInside };
          })
        )
        .subscribe((result) => {
          this.selectControl.list = result.list;
          if (!result.idInside) {
            this.selectControl.value = null;
          }
          this.area.update('control', this.selectControl.id);
        });
    });
  }

  async popAlert(message: string): Promise<boolean> {
    const result = await runInInjectionContext(
      this.worflowEditor.injector,
      async () => {
        const alertController = inject(AlertController);
        const alert = await alertController.create({
          message: message,
          buttons: [
            {
              text: 'No',
              role: 'cancel',
              handler: () => false,
            },
            {
              text: 'Yes',
              handler: () => true,
            },
          ],
        });
        await alert.present();
        return alert.onDidDismiss<boolean>()
      }
    );
    return result.role === 'cancel' ? false : true;
  }

  dataSourceChange(event: MatSelectChange): void {

  }

  async confirmChangeSource(event: MatSelectChange): Promise<boolean> {
    if (this.haveOuputConnected()) {
      const result = await this.popAlert(
        'Do you really want to change the data source? This will remove the current output connection.'
      );

      if (!result) {
        this.selectControl.value = this.selectControl.oldValue;
        event.source.writeValue(this.selectControl.oldValue);
      }
      return result;
    }
    return true;
  }


  override data() {
    const data = {
      selectDataSource: this.selectControl,
      parquetSave: this.parquetCheckbox,
    };
    return { ...super.data(), ...data };
  }

  getRevision() {
    return '123';
  }

  haveOuputConnected(): boolean {
    return this.worflowEditor
      .getConnections()
      .some((conn) => conn.source === this.id);
  }

  testConnection() {}
}
