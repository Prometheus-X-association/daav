import { $localize } from '@angular/localize/init';
import { AreaPlugin } from 'rete-area-plugin';
import { ClassicPreset } from 'rete';
import { MatSelectChange } from '@angular/material/select';
import { Schemes, AreaExtra } from 'src/app/core/workflow-editor';
import { Node } from '../../models/interfaces/node';
import { InputDataBlock } from '../input/input-data-block';
import { daavBlock } from '../node-block';
import { DeepObjectSocket } from 'src/app/core/sockets/sockets';
import { StatusNode } from 'src/app/enums/status-node';
import { PandasSchema } from 'src/app/models/dataset-schema';
import { NodeDataPandasDf } from 'src/app/models/node-data';
import { DatasetElasticSearch } from 'src/app/models/dataset-elastic-search';
import { ElasticService } from 'src/app/services/elastic.service';
import {
  SelectControl,
  selectControlI,
} from 'src/app/components/widgets/select-widget/select-widget.component';
import {
  InputAutoCompleteControl,
  inputAutoCompleteControlI,
} from 'src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component';
import {
  CheckboxControl,
  CheckboxControlI,
} from 'src/app/components/widgets/checkbox-widget/checkbox-widget.component';

const PREVIEW_SIZE = 5;
const PREVIEW_DEBOUNCE_MS = 800;

@daavBlock('input')
export class DataElasticBlock extends InputDataBlock<PandasSchema, NodeDataPandasDf> {
  override width = 350;

  selectControlIndex: SelectControl;
  queryControl: InputAutoCompleteControl;
  fieldsControl: InputAutoCompleteControl;
  maxDocsControl: InputAutoCompleteControl;
  includeIdControl: CheckboxControl;

  private node: Node;
  private elasticService: ElasticService;
  private previewTimer: ReturnType<typeof setTimeout>;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.filterInputType = [DatasetElasticSearch];
    this.elasticService = this.worflowEditor.injector.get(ElasticService);
    this.node = node;
    if (node?.data?.selectIndexDataSource) {
      this.selectControlIndex = new SelectControl(
        node.data.selectIndexDataSource,
        this.indexChange.bind(this)
      );
      this.addControl('dataIndexSource', this.selectControlIndex);
    }
    if (node?.data?.query) {
      this.addOptionControls(node);
    }
    this.area.update('node', this.id);
  }

  private get dataset(): DatasetElasticSearch {
    return this.datasetService
      .datasets()
      .find((dataset) => dataset.id === this.selectControl.value) as DatasetElasticSearch;
  }

  private get index(): string {
    return this.dataset?.index || this.selectControlIndex?.value;
  }

  override async dataSourceChange(event: MatSelectChange) {
    if (!(await this.confirmChangeSource(event))) {
      return;
    }
    this.cleanOutput();
    this.removeSelectIndex();
    this.removeOptionControls();
    const dataset = this.dataset;
    if (!dataset) {
      return;
    }
    if (dataset.index) {
      this.addOptionControls(null);
      this.refreshPreview();
      return;
    }
    this.showLoader(true);
    this.datasetService.getContentDataset(dataset, { perPage: PREVIEW_SIZE, page: 1 }, { index: null }).subscribe({
      next: (data) => {
        this.addSelectIndex(data.indices as string[]);
        this.showLoader(false);
      },
      error: (err) => {
        this.showLoader(false);
        this.updateStatus(StatusNode.Error, err?.error?.detail ?? err.message);
      },
    });
  }

  indexChange(event: MatSelectChange) {
    this.cleanOutput();
    if (event.value) {
      if (!this.queryControl) {
        this.addOptionControls(null);
      }
      this.refreshPreview();
    }
  }

  addSelectIndex(indices: string[]) {
    const selectIndex: selectControlI = {
      value: null,
      list: (indices ?? []).map((index) => ({ label: index, value: index })),
      none: true,
      label: $localize`Index`,
    };
    this.selectControlIndex = new SelectControl(selectIndex, this.indexChange.bind(this));
    this.addControl('dataIndexSource', this.selectControlIndex);
    this.area.update('control', this.selectControlIndex.id);
    this.area.update('node', this.id);
  }

  removeSelectIndex() {
    this.removeControl('dataIndexSource');
    this.selectControlIndex = null;
    if (this.node?.data?.selectIndexDataSource) {
      this.node.data.selectIndexDataSource = null;
    }
    this.area.update('node', this.id);
  }

  /** Query, fields, maximum number of documents and _id option */
  addOptionControls(node: Node) {
    const onChange = () => this.schedulePreview();
    const query: inputAutoCompleteControlI = node?.data?.query ?? {
      value: '',
      list: [],
      label: $localize`Query`,
      type: 'text',
    };
    const fields: inputAutoCompleteControlI = node?.data?.fields ?? {
      value: '',
      list: [],
      label: $localize`Fields`,
      type: 'text',
    };
    const maxDocs: inputAutoCompleteControlI = node?.data?.maxDocs ?? {
      value: '',
      list: [],
      label: $localize`Max documents`,
      type: 'number',
    };
    const includeId: CheckboxControlI = node?.data?.includeId ?? {
      value: true,
      label: $localize`Include _id`,
    };
    this.queryControl = new InputAutoCompleteControl(query, onChange);
    this.fieldsControl = new InputAutoCompleteControl(fields, onChange);
    this.maxDocsControl = new InputAutoCompleteControl(maxDocs);
    this.includeIdControl = new CheckboxControl(includeId, onChange);
    this.addControl('query', this.queryControl);
    this.addControl('fields', this.fieldsControl);
    this.addControl('maxDocs', this.maxDocsControl);
    this.addControl('includeId', this.includeIdControl);
    this.area.update('node', this.id);
  }

  removeOptionControls() {
    for (const key of ['query', 'fields', 'maxDocs', 'includeId']) {
      this.removeControl(key);
      if (this.node?.data?.[key]) {
        this.node.data[key] = null;
      }
    }
    this.queryControl = null;
    this.fieldsControl = null;
    this.maxDocsControl = null;
    this.includeIdControl = null;
    this.area.update('node', this.id);
  }

  schedulePreview() {
    clearTimeout(this.previewTimer);
    this.previewTimer = setTimeout(() => this.refreshPreview(), PREVIEW_DEBOUNCE_MS);
  }

  /** Load a sample of the query result to expose the output schema */
  refreshPreview() {
    const dataset = this.dataset;
    const index = this.index;
    if (!dataset || !index) {
      return;
    }
    const fields = (this.fieldsControl?.value ?? '')
      .split(',')
      .map((field) => field.trim())
      .filter((field) => field);
    this.showLoader(true);
    this.elasticService
      .sample(dataset.id, {
        index,
        query: this.queryControl?.value || null,
        fields: fields.length ? fields : null,
        size: PREVIEW_SIZE,
        includeId: this.includeIdControl?.value !== false,
      })
      .subscribe({
        next: (data) => {
          this.createOutput(data, index);
          this.showLoader(false);
        },
        error: (err) => {
          this.showLoader(false);
          this.updateStatus(StatusNode.Error, err?.error?.detail ?? err.message);
        },
      });
  }

  createOutput(data: NodeDataPandasDf, index: string) {
    if (!this.outputs['out']) {
      this.addOutput('out', new ClassicPreset.Output(new DeepObjectSocket(), `${index} -> Out`));
    }
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

  override data() {
    const data = {
      selectIndexDataSource: this.selectControlIndex,
      query: this.queryControl,
      fields: this.fieldsControl,
      maxDocs: this.maxDocsControl,
      includeId: this.includeIdControl,
    };
    return { ...super.data(), ...data };
  }

  override execute() {}
}
