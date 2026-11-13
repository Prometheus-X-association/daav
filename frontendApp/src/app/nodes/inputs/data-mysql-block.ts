import { Node } from 'src/app/models/interfaces/node';
import { InputDataBlock } from '../input/input-data-block';
import { AreaPlugin } from 'rete-area-plugin';
import { Schemes, AreaExtra } from 'src/app/core/workflow-editor';
import { daavBlock } from '../node-block';
import { MatSelectChange } from '@angular/material/select';
import { DatasetMySQL } from 'src/app/models/dataset-my-sql';
import { ClassicPreset } from 'rete';
import { FlatObjectSocket } from 'src/app/core/sockets/sockets';
import { StatusNode } from 'src/app/enums/status-node';
import {
  SelectControl,
  SelectControlI,
} from 'src/app/components/widgets/select-widget/select-widget.component';
import { NodeDataMysql } from 'src/app/models/node-data';
import { MysqlSchema } from 'src/app/models/dataset-schema';
import { MySQLContentResponse } from 'src/app/models/dataset-content-response';

@daavBlock('input')
export class DataMysqlBlock extends InputDataBlock<MysqlSchema, NodeDataMysql> {
  override width = 350;
  pagination = {
    perPage: 5,
    page: 1,
  };

  selectControlTable: SelectControl;
  selectControlDatabase: SelectControl;

  private readonly node: Node;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.filterInputType = [];
    this.filterInputType.push(DatasetMySQL);
    this.node = node;
    if (node?.data?.selectDatabaseDataSource) {
      this.selectControlDatabase = new SelectControl(
        node.data.selectDatabaseDataSource,
        this.dataBaseChange.bind(this)
      );
      this.addControl('dataDatabaseSource', this.selectControlDatabase);
    }
    if (node?.data?.selectTableDataSource) {
      this.selectControlTable = new SelectControl(
        node.data.selectTableDataSource,
        this.tableChange.bind(this)
      );
      this.addControl('dataTableSource', this.selectControlTable);
    }
  }

  override async dataSourceChange(event: MatSelectChange) {
    console.log('data source change', event);
    if ( !await this.confirmChangeSource(event)) {
        return;
    }
    this.cleanOutput();
    this.removeControlDatabase();
    this.removeControlTable();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find((dataset) => dataset.id === event.value) as DatasetMySQL;
      this.showLoader(true);
      this.datasetService
        .getContentDataset(dataset, this.pagination)
        .subscribe({
          next: (data) => {
            console.log(data);
            if (dataset.database) {
              if (dataset.table) {
                this.createOutput(
                  data,
                  dataset.database,
                  dataset.table,
                  dataset.id
                );
                this.status = StatusNode.Complete;
              } else {
                this.addSelectTable(data, this.node);
              }
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

  createOutput(
    data: MySQLContentResponse,
    database: string,
    table: string,
    datasetId: string
  ) {
    console.log('create output', data);
    this.addOutput(
      'out',
      new ClassicPreset.Output(new FlatObjectSocket(), `${table} -> Out`)
    );
    this.dataOutput.set('out', {
      type: 'mysql',
      datasetId,
      dataExample: data.data,
      nodeSchema: data.table_description,
      database,
      table,
      name: table,
    });
    this.updateStatus(StatusNode.Complete);
    void this.area.update('node', this.id);
  }

  cleanOutput() {
    if (this.outputs['out']) {
      const connection = this.worflowEditor
        .getConnections()
        .find((conn) => conn.source === this.id && conn.sourceOutput === 'out');
      if (connection) {
        void this.worflowEditor.removeConnection(connection.id);
      }
      this.removeOutput('out');
      this.dataOutput.delete('out');
    }
    this.updateStatus(StatusNode.Incomplete);
    void this.area.update('node', this.id);
  }

  addSelectTable(data: MySQLContentResponse, node: Node) {
    let selectTableSource: SelectControlI;
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
    data.tables.forEach((table) => {
      selectTableSource.list.push({ label: table, value: table });
    });
    if (
      selectTableSource.value &&
      !selectTableSource.list.some(
        (table) => table.value === selectTableSource.value
      )
    ) {
      selectTableSource.value = null;
    }
    this.selectControlTable = new SelectControl(
      selectTableSource,
      this.tableChange.bind(this)
    );
    this.addControl('dataTableSource', this.selectControlTable);
    void this.area.update('control', this.selectControlTable.id);
    void this.area.update('node', this.id);
  }

  addSelectDatabase(data: MySQLContentResponse, node: Node) {
    let selectDatabaseSource: SelectControlI;
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
      !selectDatabaseSource.list.some(
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
    void this.area.update('control', this.selectControlDatabase.id);
    void this.area.update('node', this.id);
  }

  removeControlDatabase() {
    this.removeControl('dataDatabaseSource');
    this.selectControlDatabase = null;
    void this.area.update('node', this.id);
    if (this.node?.data?.selectTableDataSource) {
      this.node.data.selectTableDataSource = null;
    }
  }

  removeControlTable() {
    this.removeControl('dataTableSource');
    this.selectControlTable = null;
    void this.area.update('node', this.id);
    if (this.node?.data?.selectTableDataSource) {
      this.node.data.selectTableDataSource = null;
    }
  }

  dataBaseChange(event: MatSelectChange) {
    console.log('database source change', event);
    this.removeControlTable();
    this.cleanOutput();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find(
          (dataset) => dataset.id === this.selectControl.value
        ) as DatasetMySQL;
      this.showLoader(true);
      this.datasetService
        .getContentDataset(dataset, this.pagination, {
          database: event.value,
          table: null,
        })
        .subscribe({
          next: (data) => {
            console.log(data);
            this.addSelectTable(data, this.node);
            this.showLoader(false);
          },
          error: (err) => {
            this.showLoader(false);
            console.error(err);
          },
        });
    }
  }

  tableChange(event: MatSelectChange) {
    this.cleanOutput();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find(
          (dataset) => dataset.id === this.selectControl.value
        ) as DatasetMySQL;
      const database = this.selectControlDatabase?.value
        ? this.selectControlDatabase?.value
        : dataset.database;
      this.showLoader(true);
      this.datasetService
        .getContentDataset(dataset, this.pagination, {
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
      selectTableDataSource: this.selectControlTable,
    };
    return { ...super.data(), ...data };
  }

  override execute() {
    // Intentionally empty: the data is loaded when the source is selected.
  }
}
