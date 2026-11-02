import { $localize } from '@angular/localize/init';
import { AreaPlugin } from 'rete-area-plugin';
import { ClassicPreset } from 'rete';
import { MatSelectChange } from '@angular/material/select';
import { MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { AllSocket } from 'src/app/core/sockets/sockets';
import { Schemes, AreaExtra } from 'src/app/core/workflow-editor';
import { StatusNode } from 'src/app/enums/status-node';
import { OutputDataBlock } from '../output/output-data-block';
import { Node } from 'src/app/models/interfaces/node';
import { daavBlock } from '../node-block';
import { DatasetElasticSearch } from 'src/app/models/dataset-elastic-search';
import {
  SelectControl,
  selectControlI,
} from 'src/app/components/widgets/select-widget/select-widget.component';
import {
  InputAutoCompleteControl,
  inputAutoCompleteControlI,
} from 'src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component';

@daavBlock('output')
export class ElasticOutput extends OutputDataBlock {
  override width = 350;
  override height = 156;
  private node: Node;
  indexAutoCompleteControl: InputAutoCompleteControl;
  selectExistControl: SelectControl;
  idFieldControl: InputAutoCompleteControl;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.filterInputType = [DatasetElasticSearch];
    this.node = node;
    if (!node) {
      this.status = StatusNode.Incomplete;
      // Elasticsearch indexes nested documents as well as flat rows (e.g. after a Flatten node)
      this.addInput('export', new ClassicPreset.Input(new AllSocket(), 'In'));
    }
    if (node?.data?.indexAutoComplete) {
      this.addOptionControls([], node);
    }
    this.area.update('node', this.id);
  }

  override dataSourceChange(event: MatSelectChange) {
    this.removeOptionControls();
    if (!event.value) {
      return;
    }
    const dataset = this.datasetService
      .datasets()
      .find((dataset) => dataset.id === event.value) as DatasetElasticSearch;
    this.showLoader(true);
    this.datasetService.getContentDataset(dataset, null, { index: null }).subscribe({
      next: (data) => {
        this.addOptionControls(data.indices as string[] ?? [], null, dataset.index);
        this.showLoader(false);
      },
      error: (err) => {
        this.showLoader(false);
        // Existing indices are only suggestions: the node stays usable
        this.addOptionControls([], null, dataset.index);
        console.error(err);
      },
    });
  }

  /** Target index (existing or new), behaviour when it exists and document id field */
  addOptionControls(indices: string[], node: Node, index?: string) {
    const indexAutoComplete: inputAutoCompleteControlI = node?.data?.indexAutoComplete ?? {
      value: index ?? '',
      list: indices,
      label: $localize`Index`,
      type: 'text',
    };
    this.indexAutoCompleteControl = new InputAutoCompleteControl(indexAutoComplete, (event) => {
      const filled =
        event instanceof MatAutocompleteSelectedEvent ||
        (event instanceof InputEvent && !!(event.target as HTMLInputElement).value);
      this.updateStatus(filled ? StatusNode.Complete : StatusNode.Incomplete);
    });
    this.addControl('index', this.indexAutoCompleteControl);

    const selectExist: selectControlI = node?.data?.selectExist ?? {
      value: 'fail',
      list: [
        { label: $localize`:@@exist:Fail`, value: 'fail', default: true },
        { label: $localize`:@@replace:Replace`, value: 'replace' },
        { label: $localize`:@@append:Append`, value: 'append' },
      ],
      none: false,
      label: $localize`If index already exists`,
    };
    this.selectExistControl = new SelectControl(selectExist);
    this.addControl('exist', this.selectExistControl);

    const idField: inputAutoCompleteControlI = node?.data?.idField ?? {
      value: '',
      list: [],
      label: $localize`Id field`,
      type: 'text',
    };
    this.idFieldControl = new InputAutoCompleteControl(idField);
    this.addControl('idField', this.idFieldControl);

    if (!node) {
      this.updateStatus(this.indexAutoCompleteControl.value ? StatusNode.Complete : StatusNode.Incomplete);
    }
    this.area.update('node', this.id);
  }

  removeOptionControls() {
    for (const key of ['index', 'exist', 'idField']) {
      this.removeControl(key);
    }
    for (const key of ['indexAutoComplete', 'selectExist', 'idField']) {
      if (this.node?.data?.[key]) {
        this.node.data[key] = null;
      }
    }
    this.indexAutoCompleteControl = null;
    this.selectExistControl = null;
    this.idFieldControl = null;
    this.updateStatus(StatusNode.Incomplete);
  }

  override data() {
    const data = {
      indexAutoComplete: this.indexAutoCompleteControl,
      selectExist: this.selectExistControl,
      idField: this.idFieldControl,
    };
    return { ...super.data(), ...data };
  }
}
