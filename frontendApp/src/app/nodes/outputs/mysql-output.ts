import { $localize } from '@angular/localize/init';
import { AreaPlugin } from 'rete-area-plugin';
import { FlatObjectSocket } from 'src/app/core/sockets/sockets';
import { Schemes, AreaExtra } from 'src/app/core/workflow-editor';
import { StatusNode } from 'src/app/enums/status-node';
import { OutputDataBlock } from '../output/output-data-block';
import { Node } from 'src/app/models/interfaces/node';
import { daavBlock } from '../node-block';
import {
  SelectControl,
  SelectControlI,
} from 'src/app/components/widgets/select-widget/select-widget.component';
import { DatasetMySQL } from 'src/app/models/dataset-my-sql';
import { MatSelectChange } from '@angular/material/select';
import { MySQLContentResponse } from 'src/app/models/dataset-content-response';
import { ClassicPreset } from 'rete';
import {
  InputAutoCompleteControl,
  InputAutoCompleteControlI,
} from 'src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component';
import { MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { CheckboxControl, CheckboxControlI } from 'src/app/components/widgets/checkbox-widget/checkbox-widget.component';
@daavBlock('output')
export class MysqlOutput extends OutputDataBlock {
  override width = 350;
  override height = 156;
  private readonly node: Node;
  selectControlDatabase: SelectControl;
  tableAutoCompleteControl: InputAutoCompleteControl;
  selectExistControl: SelectControl;
  indexCheckbox: CheckboxControl;
  indexTableControl: InputAutoCompleteControl;
  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.filterInputType = [];
    this.filterInputType.push(DatasetMySQL);
    this.node = node;
    if (!node) {
      this.status = StatusNode.Incomplete;
      this.addInput(
        'export',
        new ClassicPreset.Input(new FlatObjectSocket(), 'In')
      );
    }
    if (node?.data?.selectDatabaseDataSource) {
      this.selectControlDatabase = new SelectControl(
        node.data.selectDatabaseDataSource,
        this.dataBaseChange.bind(this)
      );
      this.addControl('dataDatabaseSource', this.selectControlDatabase);
      this.area.update('control', this.selectControlDatabase.id);
    }
    if (node?.data?.tableAutoComplete) {
      this.addInputTable(null,node);
    }
    if (node?.data?.selectExist) {
      this.addSelectExist(node);
    }
    this.area.update('node', this.id);
  }

  addInputTable(data: MySQLContentResponse, node: Node, table?: string) {
    let tableAutoComplete: InputAutoCompleteControlI;
    if (node?.data?.tableAutoComplete) {
      //if node is given it's an import and we report content from json
      tableAutoComplete = node.data?.tableAutoComplete;
    } else {
      tableAutoComplete = {
        value: table,
        list: [],
        label: 'Table',
        type: 'text',
      };
      tableAutoComplete.list = data.tables || [];
      if ( table){
        this.updateStatus(StatusNode.Complete);
      }
    }
    this.tableAutoCompleteControl = new InputAutoCompleteControl(
      tableAutoComplete,(event)=>{
        if (event instanceof InputEvent && (event.target as HTMLInputElement).value || event instanceof MatAutocompleteSelectedEvent){
        this.updateStatus(StatusNode.Complete);
        } else {
          this.updateStatus(StatusNode.Incomplete);
        }
      }
    );
    this.addControl('table', this.tableAutoCompleteControl);
    this.area.update('control', this.tableAutoCompleteControl.id);
    this.area.update('node', this.id);
  }


  removeInputTable() {
    this.removeControl('table');
    this.tableAutoCompleteControl = null;
    this.updateStatus(StatusNode.Incomplete);
    if (this.node?.data?.tableAutoComplete) {
      this.node.data.tableAutoComplete = null;
    }
  }

  addSelectExist(node: Node) {
    let selectExist: SelectControlI;
    if (node?.data?.selectExist) {
      //if node is given it's an import and we report content from json
      selectExist = node.data?.selectExist;
    } else {
      selectExist = {
        value: 'fail',
        list: [{label : $localize`:@@exist:Fail`, value : 'fail',default : true}, {label : $localize`:@@replace:Replace`, value : 'replace'}, {label : $localize`:@@append:Append`, value : 'append'}],
        none: false,
        label: $localize`If Table already exist`,
      };
    }
    this.selectExistControl = new SelectControl(
      selectExist
    );
    this.addControl('exist', this.selectExistControl);
    this.area.update('control', this.selectExistControl.id);
    this.area.update('node', this.id);
    let createIndex: CheckboxControlI;
    if (node?.data?.createIndex){
      createIndex = node.data?.createIndex;
    }else {
      createIndex = {
        value: false,
        label: $localize`Create Index`,
      };
    }
    this.indexCheckbox = new CheckboxControl(
      createIndex,(event)=>{
        event.checked ? this.addIndexTable(node) : this.removeIndexTable();

      }
    );
    this.addControl('createIndex', this.indexCheckbox );
    this.area.update('control', this.indexCheckbox.id);
    this.area.update('node', this.id);
  }

  removeSelectExist() {
    this.removeControl('exist');
    this.selectExistControl = null;
    if (this.node?.data?.selectExist) {
      this.node.data.selectExist = null;
    }
    this.removeControl('createIndex');
    this.indexCheckbox = null;
    if (this.node?.data?.createIndex) {
      this.node.data.createIndex = null;
    }
    this.area.update('node', this.id);
  }

  addIndexTable(node: Node){
    let indexTable: InputAutoCompleteControlI;
    if (node?.data?.indexTable) {
      //if node is given it's an import and we report content from json
      indexTable = node.data?.indexTable;
    } else {
      indexTable = {
        value: "Id",
        list: [],
        label: 'Index Table',
        type: 'text',
      };
    }
    this.indexTableControl = new InputAutoCompleteControl(
      indexTable
    );
    this.addControl('indexTable', this.indexTableControl);
    this.area.update('control', this.indexTableControl.id);
    this.area.update('node', this.id);
  }

  removeIndexTable() {
    this.removeControl('indexTable');
    this.indexTableControl = null;
    if (this.node?.data?.indexTable) {
      this.node.data.indexTable = null;
    }
    this.area.update('node', this.id);
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

  override dataSourceChange(event: MatSelectChange) {
    console.log('data source change', event);
    this.removeControlDatabase();
    this.removeInputTable();
    this.removeSelectExist();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find((dataset) => dataset.id === event.value) as DatasetMySQL;
      this.showLoader(true);
      this.datasetService.getContentDataset(dataset).subscribe({
        next: (data) => {
          console.log(data);
          if (dataset.database) {
            this.addInputTable(data, this.node, dataset.table);
            this.addSelectExist(this.node);
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

  removeControlDatabase() {
    this.removeControl('dataDatabaseSource');
    this.selectControlDatabase = null;
    this.area.update('node', this.id);
    if (this.node?.data?.selectTableDataSource) {
      this.node.data.selectTableDataSource = null;
    }
  }

  dataBaseChange(event: MatSelectChange) {
    console.log('database source change', event);
    this.removeInputTable();
    this.removeSelectExist();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find(
          (dataset) => dataset.id === this.selectControl.value
        ) as DatasetMySQL;
      this.showLoader(true);
      this.datasetService
        .getContentDataset(dataset, null, {
          database: event.value,
          table: null,
        })
        .subscribe({
          next: (data) => {
            console.log(data);
            this.addInputTable(data, this.node, dataset.table);
            this.addSelectExist(this.node);
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
      tableAutoComplete: this.tableAutoCompleteControl,
      selectExist: this.selectExistControl,
      createIndex: this.indexCheckbox,
      indexTable: this.indexTableControl,
    };
    return { ...super.data(), ...data };
  }
}
