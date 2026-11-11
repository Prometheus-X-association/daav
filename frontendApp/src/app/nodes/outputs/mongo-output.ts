import { $localize } from '@angular/localize/init';
import { AreaPlugin } from 'rete-area-plugin';
import { DeepObjectSocket } from 'src/app/core/sockets/sockets';
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
import { MongoContentResponse } from 'src/app/models/dataset-content-response';
import { ClassicPreset } from 'rete';
import {
  InputAutoCompleteControl,
  InputAutoCompleteControlI,
} from 'src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component';
import { MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { CheckboxControl, CheckboxControlI } from 'src/app/components/widgets/checkbox-widget/checkbox-widget.component';
import { DatasetMongo } from 'src/app/models/dataset-mongo';
@daavBlock('output')
export class MongoOutput extends OutputDataBlock {
  override width = 350;
  override height = 156;
  private readonly node: Node;
  selectControlDatabase: SelectControl;
  collectionAutoCompleteControl: InputAutoCompleteControl;
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
    this.filterInputType.push(DatasetMongo);
    this.node = node;
    if (!node) {
      this.status = StatusNode.Incomplete;
      this.addInput(
        'export',
        new ClassicPreset.Input(new DeepObjectSocket(), 'In')
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
    if (node?.data?.collectionAutoComplete) {
      this.addInputCollection(null,node);
    }
    if (node?.data?.selectExist) {
      this.addSelectExist(node);
    }
    this.area.update('node', this.id);
  }

  addInputCollection(data: MongoContentResponse, node: Node, collection?: string) {
    let collectionAutoComplete: InputAutoCompleteControlI;
    if (node?.data?.collectionAutoComplete) {
      //if node is given it's an import and we report content from json
      collectionAutoComplete = node.data?.collectionAutoComplete;
    } else {
      collectionAutoComplete = {
        value: collection,
        list: [],
        label: 'Collection',
        type: 'text',
      };
      collectionAutoComplete.list = data.collections || [];
      if ( collection){
        this.updateStatus(StatusNode.Complete);
      }
    }
    this.collectionAutoCompleteControl = new InputAutoCompleteControl(
      collectionAutoComplete,(event)=>{
        if (event instanceof InputEvent && (event.target as HTMLInputElement).value || event instanceof MatAutocompleteSelectedEvent){
        this.updateStatus(StatusNode.Complete);
        } else {
          this.updateStatus(StatusNode.Incomplete);
        }
      }
    );
    this.addControl('collection', this.collectionAutoCompleteControl);
    this.area.update('control', this.collectionAutoCompleteControl.id);
    this.area.update('node', this.id);
  }


  removeInputCollection() {
    this.removeControl('collection');
    this.collectionAutoCompleteControl = null;
    this.updateStatus(StatusNode.Incomplete);
    if (this.node?.data?.collectionAutoComplete) {
      this.node.data.collectionAutoComplete = null;
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
        label: $localize`If Collection already exist`,
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


  addSelectDatabase(data: MongoContentResponse, node: Node) {
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
    this.removeInputCollection();
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
            this.addInputCollection(data, this.node, dataset.table);
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
    this.removeInputCollection();
    this.removeSelectExist();
    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find(
          (dataset) => dataset.id === this.selectControl.value
        ) as DatasetMongo;
      this.showLoader(true);
      this.datasetService
        .getContentDataset(dataset, null, {
          database: event.value,
          table: null,
        })
        .subscribe({
          next: (data) => {
            console.log(data);
            this.addInputCollection(data, this.node, dataset.collection);
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
      collectionAutoComplete: this.collectionAutoCompleteControl,
      selectExist: this.selectExistControl,
      createIndex: this.indexCheckbox,
      indexTable: this.indexTableControl,
    };
    return { ...super.data(), ...data };
  }
}
