import { Node } from 'src/app/models/interfaces/node';
import { InputDataBlock } from '../input/input-data-block';
import { ClassicPreset } from 'rete';
import {
  DeepObjectSocket,
} from 'src/app/core/sockets/sockets';
import { AreaPlugin } from 'rete-area-plugin';
import { Schemes, AreaExtra } from 'src/app/core/workflow-editor';
import {
  SelectControl,
  selectControlI,
} from 'src/app/components/widgets/select-widget/select-widget.component';
import { DatasetMongo } from 'src/app/models/dataset-mongo';
import { MatSelectChange } from '@angular/material/select';
import { StatusNode } from 'src/app/enums/status-node';
import {
  MongoContentResponse,
} from 'src/app/models/dataset-content-response';
import { NodeDataPandasDf } from 'src/app/models/node-data';
import { daavBlock } from '../node-block';
import { PandasSchema } from 'src/app/models/dataset-schema';
@daavBlock('input')
export class DataMongoBlock extends InputDataBlock<PandasSchema, NodeDataPandasDf> {
  override width = 350;
  pagination = {
    perPage: 5,
    page: 1,
  };

  selectControlCollection: SelectControl;
  selectControlDatabase: SelectControl;

  private readonly node: Node;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.filterInputType = [];
    this.filterInputType.push(DatasetMongo);
    this.node = node;
    if (node?.data?.selectDatabaseDataSource) {
      this.selectControlDatabase = new SelectControl(
        node.data.selectDatabaseDataSource,
        this.dataBaseChange.bind(this)
      );
      this.addControl('dataDatabaseSource', this.selectControlDatabase);
      this.area.update('control', this.selectControlDatabase.id);
    }
    if (node?.data?.selectCollectionDataSource) {
      this.selectControlCollection = new SelectControl(
        node.data.selectCollectionDataSource,
        this.collectionChange.bind(this)
      );
      this.addControl('dataCollectionSource', this.selectControlCollection);
      this.area.update('control', this.selectControlCollection.id);
    }
    this.area.update('node', this.id);
  }

  override async dataSourceChange(event: MatSelectChange) {
    console.log('data source change', event);
    if ( !await this.confirmChangeSource(event)) {
        return;
    }
    this.cleanOutput();
    this.removeControlDatabase();
    this.removeControlCollection();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find((dataset) => dataset.id === event.value) as DatasetMongo;
      this.showLoader(true);
      if (dataset.collection) {
        this.datasetService
          .getDfContentDataset(dataset, this.pagination, {
            database: dataset.database,
            table: dataset.collection,
          })
          .subscribe({
            next: (data) => {
              console.log(data);
              this.createOutput(
                data,
                dataset.database,
                event.value,
                dataset.id
              );
              this.showLoader(false);
            },
            error: (err) => {
              this.showLoader(false);
              console.error(err);
            },
          });
      } else {
        this.datasetService
          .getContentDataset(dataset, this.pagination)
          .subscribe({
            next: (data) => {
              console.log(data);
              if (dataset.database) {
                this.addSelectCollection(data, this.node);
              } else {
                this.addSelectDatabase(data, this.node);
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
  }

  createOutput(
    data: NodeDataPandasDf,
    database: string,
    table: string,
    datasetId: string
  ) {
    this.addOutput(
      'out',
      new ClassicPreset.Output(new DeepObjectSocket(), `${table} -> Out`)
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

  addSelectCollection(data: MongoContentResponse, node: Node) {
    let selectTableSource: selectControlI;
    if (node?.data?.selectTableSource) {
      //if node is given it's an import and we report content from json
      selectTableSource = node.data?.selectDataSource;
    } else {
      selectTableSource = {
        value: null,
        list: [],
        none: true,
        label: 'Table',
      };
    }
    data.collections.forEach((table) => {
      selectTableSource.list.push({ label: table, value: table });
    });
    if (
      selectTableSource.value &&
      !selectTableSource.list.find(
        (table) => table.value === selectTableSource.value
      )
    ) {
      selectTableSource.value = null;
    }
    this.selectControlCollection = new SelectControl(
      selectTableSource,
      this.collectionChange.bind(this)
    );
    this.addControl('dataCollectionSource', this.selectControlCollection);
    this.area.update('control', this.selectControlCollection.id);
    this.area.update('node', this.id);
  }

  addSelectDatabase(data: MongoContentResponse, node: Node) {
    let selectDatabaseSource: selectControlI;
    if (node?.data?.selectDatabaseDataSource) {
      //if node is given it's an import and we report content from json
      selectDatabaseSource = node.data?.selectDatabaseDataSource;
    } else {
      selectDatabaseSource = {
        value: null,
        list: [],
        none: true,
        label: 'Database',
      };
    }
    if (data.databases) {
      selectDatabaseSource.list = [];
      data.databases.forEach((database) => {
        selectDatabaseSource.list.push({ label: database, value: database });
      });
    }
    if (
      selectDatabaseSource.value &&
      !selectDatabaseSource.list.find(
        (database) => database.value === selectDatabaseSource.value
      )
    ) {
      selectDatabaseSource.value = null;
    }
    this.selectControlDatabase = new SelectControl(
      selectDatabaseSource,
      this.dataBaseChange.bind(this)
    );
    this.addControl('dataDatabaseSource', this.selectControlDatabase);
    this.area.update('control', this.selectControlDatabase.id);
    this.area.update('node', this.id);
  }

  removeControlDatabase() {
    this.removeControl('dataDatabaseSource');
    this.selectControlDatabase = null;
    this.area.update('node', this.id);
    if (this.node?.data?.selectCollectionDataSource) {
      this.node.data.selectCollectionDataSource = null;
    }
  }

  removeControlCollection() {
    this.removeControl('dataCollectionSource');
    this.selectControlCollection = null;
    this.area.update('node', this.id);
    if (this.node?.data?.selectCollectionDataSource) {
      this.node.data.selectCollectionDataSource = null;
    }
  }

  dataBaseChange(event: MatSelectChange) {
    console.log('database source change', event);
    this.removeControlCollection();
    this.cleanOutput();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find(
          (dataset) => dataset.id === this.selectControl.value
        ) as DatasetMongo;
      this.showLoader(true);
      this.datasetService
        .getContentDataset(dataset, this.pagination, {
          database: event.value,
          table: null,
        })
        .subscribe({
          next: (data) => {
            console.log(data);
            this.addSelectCollection(data, this.node);
            this.showLoader(false);
          },
          error: (err) => {
            this.showLoader(false);
            console.error(err);
          },
        });
    }
  }

  collectionChange(event: MatSelectChange) {
    this.cleanOutput();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find(
          (dataset) => dataset.id === this.selectControl.value
        ) as DatasetMongo;
      const database = this.selectControlDatabase?.value
        ? this.selectControlDatabase?.value
        : dataset.database;
      this.showLoader(true);
      this.datasetService
        .getDfContentDataset(dataset, this.pagination, {
          database: database,
          table: event.value,
        })
        .subscribe({
          next: (data) => {
            console.log(data);
            this.createOutput(data, database, event.value, dataset.id);
            this.showLoader(false);
          },
          error: (err) => {
            this.showLoader(false);
            console.error(err);
          },
        });
    }
  }

  override data() {
    const data = {
      selectDatabaseDataSource: this.selectControlDatabase,
      selectCollectionDataSource: this.selectControlCollection,
    };
    return { ...super.data(), ...data };
  }

  override execute() {}
}
