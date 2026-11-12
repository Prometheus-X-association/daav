import { runInInjectionContext, inject } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import {
  SelectControlI,
  SelectControl,
} from 'src/app/components/widgets/select-widget/select-widget.component';
import { Dataset } from 'src/app/models/dataset';
import { DatasetService } from 'src/app/services/dataset.service';
import { NodeBlock } from '../node-block';
import { OutputNodeComponent } from 'src/app/components/nodes/output/nodes.component';
import { Node } from "src/app/models/interfaces/node";
import { MatSelectChange } from '@angular/material/select';
import { AreaPlugin } from 'rete-area-plugin';
import { Schemes, AreaExtra } from 'src/app/core/workflow-editor';
import { WorkflowNodeEditor } from 'src/app/core/workflow-node-editor';
import { HttpClient } from '@angular/common/http';

export class OutputDataBlock extends NodeBlock {

  selectControl: SelectControl;
  datasetService: DatasetService;
  http: HttpClient;
  worflowEditor: WorkflowNodeEditor<Schemes>;
  selectDataSourceSub: any;
  filterInputType: any;
  constructor(label:string,area : AreaPlugin<Schemes, AreaExtra>,node?:Node){
      super(label,area,node)
      this.worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
      //retrieve dataset service from injector
      this.datasetService = this.worflowEditor.injector.get(DatasetService);
      this.http = this.worflowEditor.injector.get(HttpClient);
      this.addSourceSelect(node);

  }

  override getNodeComponent(): any {
    return OutputNodeComponent;
  }

   addSourceSelect(node: Node) {
    let selectDataSource: SelectControlI;
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
    void this.area.update('control', this.selectControl.id);
    //update list from service on dataset signal
    // this is obscur toObservable have problem context and need to run in runInInjectionContext
    runInInjectionContext(this.worflowEditor.injector, () => {
      const service = inject(DatasetService);
      this.selectDataSourceSub = toObservable(service.datasets)
        .pipe(
          map((params) => {
            const list = [];
            let idInside = false;
            if (this.filterInputType) {
              params = params.filter(this.datasetFilter.bind(this));
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
        .subscribe(this.updateSourceSelectResult.bind(this));
    });
  }

  protected updateSourceSelectResult(result) {
    this.selectControl.list = result.list;
    
    // Vérifier si nous avons une valeur sélectionnée dans les données
    const currentData = this.data();
    if (currentData?.selectDataSource?.value) {
        // Forcer la mise à jour de la valeur du select
        this.selectControl.value = currentData.selectDataSource.value;
        // Garder le label "Dataset"
        this.selectControl.label = "Dataset";
    } else if (!result.idInside) {
        this.selectControl.value = null;
    }

    // Forcer la mise à jour du contrôle
    void this.area.update('control', this.selectControl.id);
    void this.area.update('node', this.id);
  }

  protected datasetFilter(dataset : Dataset){
    return this.filterInputType.some((type) => dataset instanceof type)
  }

  dataSourceChange(event : MatSelectChange){
    console.log('data source change',event);
  }

  override data() {
    const data = { selectDataSource: this.selectControl };
    return { ...super.data(), ...data };
  }

  override getRevision(): string {
    throw new Error('Method not implemented.');
  }

}
