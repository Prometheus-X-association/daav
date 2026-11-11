import { AreaPlugin } from "rete-area-plugin";
import { OutputDataBlock } from "../output/output-data-block";
import { AreaExtra, Schemes } from "src/app/core/workflow-editor";
import { StatusNode } from "src/app/enums/status-node";
import { ClassicPreset } from "rete";
import { FlatObjectSocket } from "src/app/core/sockets/sockets";
import { Node } from "src/app/models/interfaces/node";
import { daavBlock } from "../node-block";
import { DatasetFile } from "src/app/models/dataset-file";
import { MatSelectChange } from "@angular/material/select";
import {
  SelectControl,
  SelectControlI,
} from 'src/app/components/widgets/select-widget/select-widget.component';
import {
  InputAutoCompleteControl,
  InputAutoCompleteControlI,
} from 'src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component';
import { Dataset } from "src/app/models/dataset";


@daavBlock('output')
export class FileOutput extends OutputDataBlock {
  override width = 350;
  override height = 156;
  private readonly node: Node;
  delimiterControl: SelectControl;
  fileTypeControl: SelectControl;
  fileNameControl: InputAutoCompleteControl;
  fileExistControl: SelectControl;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.filterInputType = [];
    this.filterInputType.push(DatasetFile);
    this.node = node;
    if (!node) {
      this.status = StatusNode.Incomplete;
      this.addInput(
        'export',
        new ClassicPreset.Input(new FlatObjectSocket(), 'In')
      );
      this.selectControl.new= true;
      this.selectControl.none= false;
      this.addFileNameControl();
      this.addFileTypeControl();
    } else {
      this.selectControl.new= true;
      // If node is given, we are importing from JSON
      if (node.data?.fileName && !node.data?.selectDataSource.value) {
        this.addFileNameControl(node);
      }
      if (node.data?.delimiter) {
        this.addDelimiterControl(node);
      }
      if (node.data?.fileType) {
        this.addFileTypeControl(node.data.fileType.value);

      }
      if (node.data?.fileExist) {
        this.addFileExistControl(node);

      }
    }
  }

  addFileNameControl(node? : Node) {
    let fileNameOptions: InputAutoCompleteControlI = {
      value: '',
      label: 'File Name',
      list: [],
      type: 'text'
    };

    // Pass the onChange function as second parameter
    if(node?.data?.fileName){
      fileNameOptions.value = node?.data?.fileName.value
    }

    this.fileNameControl = new InputAutoCompleteControl(
      fileNameOptions,
      this.checkAndUpdateStatus.bind(this)
    );

    this.addControl('fileName', this.fileNameControl);
    this.area.update('control', this.fileNameControl.id);
    this.area.update('node', this.id);
  }

  addDelimiterControl(node? : Node) {
    if (this.delimiterControl) return;
    const delimiterOptions: SelectControlI = {
      value: ',',
      list: [
        { label: 'Comma (,)', value: ',' },
        { label: 'Semicolon (;)', value: ';' },
        { label: 'Tab (\\t)', value: '\t' },
      ],
      none: false,
      label: 'Delimiter',
    };
    this.delimiterControl = new SelectControl(node?.data?.delimiterControl?node.data.delimiterControl : delimiterOptions);
    this.addControl('delimiter', this.delimiterControl);
    this.area.update('control', this.delimiterControl.id);
    this.area.update('node', this.id);
  }

  addFileTypeControl(type? : string) {
    const fileTypeOptions: SelectControlI = {
      value: type || 'csv',
      list: [
        { label: 'CSV', value: 'csv' },
        { label: 'JSON', value: 'json' },
        { label: 'XML', value: 'xml' },
        { label: 'PARQUET', value: 'parquet' },
      ],
      label: 'File Type',
    };
    this.fileTypeControl = new SelectControl(fileTypeOptions,this.fileControlChange.bind(this));
    this.addControl('fileType', this.fileTypeControl);
    this.area.update('control', this.fileTypeControl.id);
    this.area.update('node', this.id);
    if (fileTypeOptions.value === 'csv') {
      this.addDelimiterControl();
    }
  }

    addFileExistControl(node? : Node) {
    const fileTypeOptions: SelectControlI = {
      value: 'replace',
      list: [
        { label: 'Replace', value: 'replace' },
        { label: 'Append', value: 'append' }
      ],
      none: false,
      label: 'If File Exist',
    };
    this.fileExistControl = new SelectControl(node?.data?.fileExist ? node.data.fileExist: fileTypeOptions,this.fileControlChange.bind(this));
    this.addControl('fileExist', this.fileExistControl);
    this.area.update('control', this.fileExistControl.id);
    this.area.update('node', this.id);
  }

  /**
   * Extract file extension from file path
   * @param filePath - The file path to extract extension from
   * @returns the file extension in lowercase or empty string if none
   */
  private extractFileExtension(filePath: string): string {
    if (!filePath) return '';

    const extension = filePath.toLowerCase().split('.').pop();
    return extension || '';
  }

  /**
   * Check if file path has a valid extension for file output
   * @param filePath - The file path to check
   * @returns true if the file has a valid extension (csv, json, xml)
   */
  private hasValidFileExtension(filePath: string): boolean {
    const validExtensions = ['csv', 'json', 'xml', 'parquet'];
    const extension = this.extractFileExtension(filePath);

    return validExtensions.includes(extension);
  }

  /**
   * Get file type from file path extension
   * @param filePath - The file path to analyze
   * @returns the file type matching the extension or 'csv' as default
   */
  private getFileTypeFromPath(filePath: string): string {
    const extension = this.extractFileExtension(filePath);

    // Map extensions to file types
    const extensionMap: { [key: string]: string } = {
      'csv': 'csv',
      'json': 'json',
      'xml': 'xml',
      'parquet': 'parquet',
    };

    return extensionMap[extension] || 'csv';
  }

  /**
   * Check and update node status based on current configuration
   * Updates status to Complete if fileName is filled or dataset is selected, Incomplete otherwise
   */
  private checkAndUpdateStatus(): void {
    const hasFileName = this.fileNameControl?.value && this.fileNameControl.value.trim() !== '';
    const hasDataset = this.selectControl?.value;

    if (hasDataset || hasFileName) {
      this.updateStatus(StatusNode.Complete);
    } else {
      this.updateStatus(StatusNode.Incomplete);
    }
  }

  override dataSourceChange(event: MatSelectChange): void {
    console.log('data source change file');
    this.removeControl('delimiter');
    this.removeControl('fileName');
    this.removeControl('fileType');
    this.removeControl('fileExist');
    this.delimiterControl = null;
    this.fileNameControl = null;
    this.fileTypeControl = null;
    this.fileExistControl = null;
    this.area.update('node', this.id);

    if (event.value) {
      const dataset = this.datasetService
        .datasets()
        .find((dataset) => dataset.id === event.value) as DatasetFile;
      console.log(dataset)
      const fileType = this.getFileTypeFromPath(dataset.filePath || '');
      this.addFileExistControl();
      this.addFileTypeControl(fileType);
    } else {
      this.addFileNameControl();
      this.addFileTypeControl();
    }

    // Check status in all cases
    this.checkAndUpdateStatus();
  }

  fileControlChange(event: MatSelectChange) {
    console.log('file type change', event);
    if (event.value === 'csv') {
      this.addDelimiterControl();
    } else {
      this.removeControl('delimiter');
      this.delimiterControl = null;
      this.area.update('node', this.id);
    }
  }

  override datasetFilter(dataset : Dataset){
    return dataset instanceof DatasetFile && !dataset.folder && this.hasValidFileExtension(dataset.filePath);
  }

  override processNodeResponse(response: any) {
    if (response?.data?.selectDataSource) {
      const newDataSource = response.data.selectDataSource;
      
      // Fetch the newly created dataset
      this.datasetService.getDatasets().subscribe(datasets => {
        const newDataset = datasets.find(d => d.id === newDataSource.value);
        if (newDataset) {
          // Add to dataset service list
          this.datasetService.addDatasetToList(newDataset);
          
          // Update select control
          this.selectControl.value = newDataSource.value;

          // Remove fileName control since we now have a dataset
          if (this.fileNameControl) {
            this.removeControl('fileName');
            this.fileNameControl = null;
          }

          // Update the view
          this.area.update('control', this.selectControl.id);
          this.area.update('node', this.id);
        }
      });
    }
  }

  override data() {
    const data = {
      fileType: this.fileTypeControl,
      delimiter: this.delimiterControl,
      fileName: this.fileNameControl,
      fileExist: this.fileExistControl
    };
    return { ...super.data(), ...data };
  }
}
