import { Input, Output } from "@angular/core";
import { daavBlock } from "../node-block";
import { OutputDataBlock } from "../output/output-data-block";
import { AreaPlugin } from "rete-area-plugin";
import { AreaExtra, Schemes } from "src/app/core/workflow-editor";
import { Node } from 'src/app/models/interfaces/node';
import { WorkflowNodeEditor } from "src/app/core/workflow-node-editor";
import { DatasetPTX } from "src/app/models/dataset-ptx";
import { StatusNode } from "src/app/enums/status-node";
import { ClassicPreset } from "rete";
import { AllSocket } from "src/app/core/sockets/sockets";
import { MatSelectChange } from "@angular/material/select";
import { SelectControl, selectControlI } from "src/app/components/widgets/select-widget/select-widget.component";
import { InputAutoCompleteControl, inputAutoCompleteControlI } from "src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component";
import { ButtonControl } from "src/app/components/widgets/button-widget/button-widget.component";
import { TextDisplayControl, textDisplayControlI } from "src/app/components/widgets/text-display-widget/text-display-widget.component";
import { MatAutocompleteSelectedEvent } from "@angular/material/autocomplete";


@daavBlock("output")
export class PdcOutput extends OutputDataBlock {
  override width = 350;
  private node: Node;

  private dataResourcesResponse: any;
  private selectControlDataResource: SelectControl;
  private urlInputControl: InputAutoCompleteControl;
  private saveUrlButton: ButtonControl;
  private currentUrlControl: TextDisplayControl;

  constructor(
    label: string, 
    area: AreaPlugin<Schemes, AreaExtra>, 
    node?: Node) {
      super(label, area, node);
      this.worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
      this.filterInputType = [];
      this.filterInputType.push(DatasetPTX);
      this.node = node;

      if (!node){
        this.status = StatusNode.Incomplete;
        this.addInput(
          "in",
          new ClassicPreset.Input(new AllSocket(), "in")
        );
      }
      
      if(node?.data?.selectDataResource){
        this.selectControlDataResource = new SelectControl(
          node.data.selectDataResource,
          this.dataResourceChange.bind(this)
        );
        this.addControl("selectDataResource", this.selectControlDataResource);
        this.area.update('control', this.selectControlDataResource.id);
      }

      this.loadDataResourcesAndInitialize(node);

      if (node?.data?.currentUrl) {
        this.addCurrentUrlControl(node.data.currentUrl.value);
      }else {
        this.removeCurrentUrlControl();
      }

      if (node?.data?.urlInput) {
        this.addUrlControl(node.data.urlInput.value, node);
      } else {
        this.removeUrlControl();
      }

      this.area.update('node', this.id);
    }

    private addCurrentUrlControl(url?: string): void {
      const currentUrl = url || window.location.href;
      
      const currentUrlData: textDisplayControlI = {
        value: currentUrl,
        label: 'Current URL',
        copyable: true,
      };
      
      this.currentUrlControl = new TextDisplayControl(currentUrlData);
      this.addControl('currentUrl', this.currentUrlControl);
      this.area.update('control', this.currentUrlControl.id);
      this.area.update('node', this.id);
    }

    private removeCurrentUrlControl(): void {
      if (this.currentUrlControl) {
        this.removeControl('currentUrl');
        this.currentUrlControl = null;
        this.area.update('node', this.id);
      }
    }

    private updateCurrentUrlDisplay(newUrl: string): void {
      if (this.currentUrlControl) {
        this.currentUrlControl.value = newUrl;
        this.area.update('control', this.currentUrlControl.id);
      }
    }

    private formatResourceNameAsFileName(resourceName: string): string {
      if (!resourceName) return '';
      
      return resourceName
        .toLowerCase()
        .trim()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9\-_\.]/g, '') 
        .replace(/\-+/g, '-') 
        .replace(/^-|-$/g, ''); 
    }

    private loadDataResourcesAndInitialize(node: Node): void {
      if (node?.data?.selectDataResource?.value && this.selectControl?.value) {
        const dataset = this.datasetService
          .datasets()
          .find((ds) => ds.id === this.selectControl.value) as DatasetPTX;
          
        if (dataset) {
          this.http.get(this.datasetService.urlBack + "/ptx/dataResources/" + dataset.id).subscribe({
            next: (data) => {
              this.dataResourcesResponse = data;
              
              this.dataResourceChange({ value: node.data.selectDataResource.value } as MatSelectChange);
            },
            error: (error) => {
              console.error("Can't load dataResources", error);
            }
          });
        }
      }
    }

    override dataSourceChange(event: MatSelectChange): void {
      console.log("PDC Output data source change", this.selectControl);
      this.removeControlDataSource();
      
      if(event.value){
        const dataset = this.datasetService
          .datasets()
          .find((ds) => ds.id === event.value) as DatasetPTX;
        this.http.get(this.datasetService.urlBack + "/ptx/dataResources/" + dataset.id ).subscribe({
          next: (data) => {
            this.dataResourcesResponse = data;
            this.addSelectControlDataResource(data);
          }
        })
        
      }
    }

    removeControlDataSource(): void {
      this.removeControl("selectDataResource");
      this.removeUrlControl();
      this.removeSaveButton();
      this.selectControlDataResource = null;
      this.area.update('node', this.id);
    }

    addSelectControlDataResource(data, node?: Node) {
      let selectDataResource: selectControlI;

      if (node?.data?.selectDataResource) {
        // If node is given, it's an import and we report content from JSON
        selectDataResource = node.data?.selectDataResource;
      } else {
        selectDataResource = {
          value: null,
          list: [],
          none: true,
          label: 'DataResource'
        };
        if (data && Array.isArray(data.dataResources)) {
          selectDataResource.list = [];
          data.dataResources.forEach((resource) => {
            selectDataResource.list.push({
              label: resource.name,
              value: resource._id
            });
          });
        }
      }
      
      if (
        selectDataResource.value &&
        !selectDataResource.list.find(
          (resource) => resource.value === selectDataResource.value
        )
      ) {
        selectDataResource.value = null;
      }
    
      this.selectControlDataResource = new SelectControl(
        selectDataResource,
        this.dataResourceChange.bind(this) 
      );

      this.addControl("selectDataResource", this.selectControlDataResource)
      this.area.update('control', this.selectControlDataResource.id);
      this.area.update('node', this.id);
    }

    dataResourceChange(event: MatSelectChange): void {
      console.log("PDC Output data resource change", event);
      this.removeUrlControl();
      
      if (event.value) {
        if (this.dataResourcesResponse?.dataResources) {
          this.processDataResourceSelection(event.value);
        } else {
          const dataset = this.datasetService
            .datasets()
            .find((ds) => ds.id === this.selectControl.value) as DatasetPTX;
            
          if (dataset) {
            this.http.get(this.datasetService.urlBack + "/ptx/dataResources/" + dataset.id).subscribe({
              next: (data) => {
                this.dataResourcesResponse = data;
                this.processDataResourceSelection(event.value);
              },
              error: (error) => {
                console.error("Can't load dataResources", error);
              }
            });
          }
        }
      } else {
        this.removeUrlControl();
      }
    }

    private addUrlControl(url?: string, node?: Node): void {
      let urlControlData: inputAutoCompleteControlI; 
      if(node?.data?.urlInput) {
        urlControlData = { ...node.data.urlInput };
        
        if (urlControlData.value && urlControlData.value.includes('://')) {
          const { baseUrl, fileName } = this.extractUrlParts(urlControlData.value);
          urlControlData.value = fileName; 
          urlControlData.label = baseUrl;  
        }
      } else {
        const { baseUrl, fileName } = this.extractUrlParts(url);
        
        urlControlData = {
          value: fileName, 
          label: this.datasetService.urlBack + '/output/',  
          type: 'text',
          list: [],
        }
      }
      
      this.urlInputControl = new InputAutoCompleteControl(
        urlControlData,
        this.urlChange.bind(this)
      );
  
      this.addControl('urlText', this.urlInputControl);
      this.area.update('control', this.urlInputControl.id);
      this.area.update('node', this.id);
  
      if (urlControlData.value) {
        this.updateStatus(StatusNode.Complete);
        this.addSaveButton();
      }
    }

    private addSaveButton(disabled: boolean = true): void {
      this.removeSaveButton();
      this.saveUrlButton = new ButtonControl(
        this.saveUrlModification.bind(this),
        'Save URL',
        '',
        disabled ? 'url-save-button-disabled' : 'url-save-button',
        disabled
      );
      this.addControl('saveUrlButton', this.saveUrlButton);
      this.area.update('control', this.saveUrlButton.id);
      this.area.update('node', this.id);
    }

    private extractUrlParts(fullUrl?: string): { baseUrl: string, fileName: string } {
      if (!fullUrl) {
        return {
          baseUrl: this.datasetService.urlBack + '/output/',
          fileName: ''
        };
      }
    
      if (fullUrl.includes('://')) {
        try {
          const url = new URL(fullUrl);
          const pathParts = url.pathname.split('/');
          const fileName = pathParts[pathParts.length - 1] || '';
          const baseUrl = fullUrl.substring(0, fullUrl.lastIndexOf('/') + 1);
          
          return {
            baseUrl: baseUrl,
            fileName: fileName
          };
        } catch (error) {
          return {
            baseUrl: this.datasetService.urlBack + '/output/',
            fileName: fullUrl
          };
        }
      }
    
      const backendUrl = this.datasetService.urlBack + '/output';
      
      if (fullUrl.startsWith(backendUrl)) {
        let remainingPath = fullUrl.substring(backendUrl.length);
        
        if (remainingPath.startsWith('/')) {
          remainingPath = remainingPath.substring(1);
        }
        
        return {
          baseUrl: backendUrl + '/',
          fileName: remainingPath 
        };
      } else {
        return {
          baseUrl: this.datasetService.urlBack + '/output/',
          fileName: fullUrl
        };
      }
    }
    

    private saveUrlModification(): void {
      const baseUrl = this.urlInputControl?.label || this.datasetService.urlBack + '/output/';
      const fileName = this.urlInputControl?.value || '';
      
      let newUrl: string;
      
      if (baseUrl.includes('://')) {
        newUrl = baseUrl + fileName;
      } else {
        newUrl = baseUrl + fileName;
      }
      
      if (this.selectControlDataResource?.value && newUrl) {
        const payload = {
          dataResourceId: this.selectControlDataResource.value,
          newUrl: newUrl
        }
        this.http.put(this.datasetService.urlBack + "/ptx/dataResources/" + this.selectControl.value, payload).subscribe({
          next: (response) => {            
            this.updateCurrentUrlDisplay(newUrl);
            
          },
          error: (error) => {
            console.error("Error saving URL modification", error);
          }
        })
        this.addSaveButton();
      }
    }

    private removeSaveButton(): void {
      if (this.saveUrlButton) {
        this.removeControl('saveUrlButton');
        this.saveUrlButton = null;
        this.area.update('node', this.id);
      }
    }

    private removeUrlControl(): void {
      this.removeCurrentUrlControl();
      if (this.urlInputControl) {
        this.removeControl('urlText');
        this.urlInputControl = null;
        this.area.update('node', this.id);
      }
    }

    urlChange(event: any): void {
      if (event instanceof InputEvent && (event.target as HTMLInputElement).value ){
        this.toggleSaveButtonState(false)
        this.updateStatus(StatusNode.Complete);
      } else {
        this.updateStatus(StatusNode.Incomplete, "URL Empty");
      }
    }
    private toggleSaveButtonState(disabled: boolean): void {
      if (this.saveUrlButton) {
          this.saveUrlButton.disabled = disabled;
          this.saveUrlButton.disabled = disabled;
          this.saveUrlButton.className = disabled ? 'url-save-button-disabled' : 'url-save-button';
      } else {
          this.addSaveButton(disabled);
      }
  }
  

    private processDataResourceSelection(resourceId: string): void {
      if (this.dataResourcesResponse?.dataResources) {
        const selectedResource = this.dataResourcesResponse.dataResources.find(
          resource => resource._id === resourceId
        );
        
        if (selectedResource) {
          const url = selectedResource.representation?.url;
    
          if (url) {
            this.updateStatus(StatusNode.Complete);
            this.addCurrentUrlControl(url)
            this.addUrlControl(url);
          } else {
            const defaultFileName = this.formatResourceNameAsFileName(selectedResource.name);
            const defaultUrl = this.datasetService.urlBack + '/output/' + defaultFileName;
            this.addCurrentUrlControl(defaultUrl)
            this.addUrlControl(defaultUrl);
          }
        } 
      }
    }

    override data() {
      const data = {
       selectDataResource: this.selectControlDataResource,
       urlInput: this.urlInputControl,
       currentUrl: this.currentUrlControl,
      };
      return { ...super.data(), ...data };
    }

}