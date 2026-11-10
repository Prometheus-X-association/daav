import { PandasSchemaUtils } from '../../models/dataset-schema';
import { PandasSchema } from "src/app/models/dataset-schema";
import { NodeDataPandasDf } from "src/app/models/node-data";
import { daavBlock} from "../node-block";
import { InputDataBlock } from "../input/input-data-block";
import { DatasetPTX } from "src/app/models/dataset-ptx";
import { Node } from 'src/app/models/interfaces/node';
import { AreaPlugin } from "rete-area-plugin";
import { AreaExtra, Schemes } from "src/app/core/workflow-editor";
import { ClassicPreset } from "rete";
import { JsonInputsControl } from "src/app/components/widgets/json-inputs-widget/json-inputs-widget.component";
import { IonModalCustomEvent, OverlayEventDetail } from "@ionic/core";
import { WorkflowNodeEditor } from "src/app/core/workflow-node-editor";
import { DeepObjectSocket, FlatObjectSocket, SimpleFieldSocket } from "src/app/core/sockets/sockets";
import { StatusNode } from "src/app/enums/status-node";
import { MatSelectChange } from '@angular/material/select';
import { SelectControl, selectControlI } from 'src/app/components/widgets/select-widget/select-widget.component';
import { ButtonControl } from 'src/app/components/widgets/button-widget/button-widget.component';


@daavBlock('input')
export class ServiceChainInput extends InputDataBlock<PandasSchema, NodeDataPandasDf> {

  private readonly node: Node;
  override width = 250;
  inputsDatasource: JsonInputsControl;
  private serviceChainControl: SelectControl;
  private triggerButton: ButtonControl;

  private currentContractId: string;
  private currentServiceChainId: string;
  private serviceChainData: any;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ) {
    super(label, area, node);
    this.worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
    this.filterInputType = [];
    this.filterInputType.push(DatasetPTX);
    this.node = node;
    if (node?.data?.inputsDatasource) {
      this.inputsDatasource = new JsonInputsControl(
        node?.data?.inputsDatasource,
        this.inputsDataChange.bind(this)
      );
    } else {
      this.inputsDatasource = new JsonInputsControl(
        node?.data?.inputsDatasource,
        this.inputsDataChange.bind(this)
      );
    }
    if(node?.data?.selectServiceChainControl){
      this.addSelectControlServiceChain(null, node)
    }

    if (node?.data?.currentContractId && node?.data?.currentServiceChainId) {
      this.currentContractId = node.data.currentContractId;
      this.currentServiceChainId = node.data.currentServiceChainId;
      this.addTriggerButton()
    }

    this.addControl('inputsDatasource', this.inputsDatasource);
    this.area.update('control', this.inputsDatasource.id);
    this.area.update('node', this.id);
  }

  override dataSourceChange(event: MatSelectChange): void {
    console.log("PDC data source change")
    this.removeControlServiceChain()
    this.removeTriggerButton()
    if(event.value){
      const dataset = this.datasetService
       .datasets()
       .find((ds) => ds.id == event.value) as DatasetPTX;
       this.http.get(this.datasetService.urlBack + "/ptx/serviceChain/" + dataset.id).subscribe({
        next: (data) => {
          this.addSelectControlServiceChain(data);
        }
       })
    }
  }

  addSelectControlServiceChain(data, node?: Node){
    let selectServiceChain: selectControlI;

    if(node?.data?.selectServiceChainControl){
      selectServiceChain = node?.data?.selectServiceChainControl;
    }else {
      selectServiceChain = {
        value: null,
        list: [],
        none: true,
        label: 'Service Chain'
      };
      if(data) {
        selectServiceChain.list = [];
        data.forEach((item) => 
          item.service_chains
            .filter((serviceChain) => serviceChain.status === "Active")
            .forEach((serviceChain) => {
                selectServiceChain.list.push({
                    label: serviceChain.name,
                    value: serviceChain._id,
                    data: item.contract_id
                });
            })
        )
    }
    }
    this.serviceChainControl = new SelectControl(
      selectServiceChain,
      this.serviceChainChanged.bind(this) 
    );

    this.addControl("selectServiceChain", this.serviceChainControl)
    this.area.update('control', this.serviceChainControl.id);
    this.area.update('node', this.id);
  } 

  serviceChainChanged(event: MatSelectChange){
    console.log("service chain changed")
    if(event.value){
      this.currentServiceChainId = event.value;
      const selectedOption = this.serviceChainControl.list.find(item => item.value === event.value);
     
      if(selectedOption?.data) {
        this.currentContractId = selectedOption.data;
      }

      this.removeTriggerButton()
      this.addTriggerButton()
    }
    else{
      this.removeTriggerButton()
    }
  }

  private addTriggerButton(): void {
    this.triggerButton = new ButtonControl(
      this.triggeredServiceChain.bind(this),
      "Trigger exchange",
      '',
      'url-save-button',
    )
    this.addControl("triggerButton", this.triggerButton);
    this.area.update("control", this.triggerButton.id);
    this.area.update('node', this.id);
  }

  removeTriggerButton(){
    this.removeControl("triggerButton");
    this.area.update('node', this.id)
  }

  triggeredServiceChain(){
    console.log("button clicked")
    if(this.serviceChainControl?.value){
      const payload = {
        contractId: this.currentContractId, 
        serviceChainId: this.serviceChainControl.value
      }
      this.http.post(this.datasetService.urlBack + "/ptx/triggerServiceChain/" + this.selectControl.value, payload).subscribe({
      next: (response: any) => { 
        
        if(response.response.content.success){
          window.alert("Service Chain triggered successfully")
          this.loadServiceChainData()
        }
        else {
          window.alert('Failed to trigger service chain')
        }
      },
        error: (error) => {
          console.error("Error saving URL modification", error);
        }
      })
    }
  }
  
  loadServiceChainData(){
      this.http.get(this.datasetService.urlBack + "/ptx/serviceChain/data/" + this.currentServiceChainId).subscribe({
        next: (res: any) => {     
          this.serviceChainData = res.data
          
          if (!this.inputsDatasource.inputsDataExample) {
            this.inputsDatasource.inputsDataExample = [];
          }
         
          this.inputsDatasource.inputsDataExample = [
            ...this.inputsDatasource.inputsDataExample,
            ...this.serviceChainData
          ]

          this.removeServiceChainData(this.currentServiceChainId)
        },
        error: (error) => {
          console.error("Error retrieving service chain data", error);
        }
      })

      this.area.update('control', this.inputsDatasource.id);
      this.area.update('node', this.id);
    }

    removeServiceChainData(service_chain_id: string){
      this.http.delete(this.datasetService.urlBack + "/ptx/serviceChain/data/remove/" + service_chain_id).subscribe({
        next: (res) => {
          this.serviceChainData = []
          console.log("Success deleting service chain data ")
        },
        error: (e) => {
          console.log("Error deleting service chain data")
        }
      })
    }

  removeControlServiceChain(){
    this.removeControl("selectServiceChain");
    this.serviceChainControl = null;
    this.area.update('node', this.id)
  }

  inputsDataChange(evt : IonModalCustomEvent<OverlayEventDetail<boolean>>){
    console.log('input number change',this.inputsDatasource.inputsDataExample);
    console.log('event',evt);
    //component data have changed
    if (evt.detail.data) {
      this.createOutputs();

    }
  }

  createOutputs() {
    if (this.inputsDatasource?.inputsDataExample) {
      let pendingRequests = 0;
      let hasErrors = false;

      try {
        this.showLoader(true);
        this.cleanOuputs();
        pendingRequests = this.inputsDatasource.inputsDataExample.length;

        for (let index = 0; index < this.inputsDatasource.inputsDataExample.length; index++) {
          const input = this.inputsDatasource.inputsDataExample[index];
          const labelName = `Pdc chain data[${index}]`;
          const outputName = `pdc-${index}`;

          this.processInput(input, outputName, labelName, index, () => {
            pendingRequests--;
            if (pendingRequests === 0) {
              this.showLoader(false);
              if (hasErrors) {
                console.error('Errors have occurred during processing inputs.');
                this.updateStatus(StatusNode.Incomplete);
                this.area.update('node', this.id);
              } else {
                this.updateStatus(StatusNode.Complete);
                this.area.update('node', this.id);
              }
            }
          }, () => {
            hasErrors = true;
            pendingRequests--;
            if (pendingRequests === 0) {
              this.showLoader(false);
            }
          });
        }
      } catch (error) {
        console.error('Error creating outputs:', error);
        this.showLoader(false);
      }
    }
  }

  // Helper method to process each input
  private processInput(
    input: any,
    outputName: string,
    labelName: string,
    index: number,
    onComplete: () => void,
    onError: () => void
  ) {
    this.datasetService
      .getDfFromJson(input)
      .subscribe({
        next: (data) => {
          console.log(`Processed input ${index}:`, data);
          this.addOutput(outputName, new ClassicPreset.Output(PandasSchemaUtils.isDeepObjectSchema(data.nodeSchema)?new DeepObjectSocket(): new FlatObjectSocket(), labelName));
          this.area.update('node', this.id);
          this.dataOutput.set(outputName, data);
          onComplete();
        },
        error: (err) => {
          console.error(`Error processing input ${index}:`, err);
          // Ajouter une sortie avec indication d'erreur
          this.addOutput(outputName, new ClassicPreset.Output(new SimpleFieldSocket(), `${labelName} (ERROR)`));
          this.area.update('node', this.id);
          onError();
        }
      });
  }

  cleanOuputs(){
    Object.entries(this.outputs).forEach(([key, input]) => {
      const connection = this.worflowEditor.getConnections().find(conn => conn.source === this.id && conn.sourceOutput === key);
      if (connection){
        this.worflowEditor.removeConnection(connection.id);
      }
      this.removeOutput(key);
      this.dataOutput.delete(key);
    });
  }

  override data() {
    const data = {
      inputsDatasource: this.inputsDatasource.inputsDataExample,
      selectServiceChainControl: this.serviceChainControl,
      currentContractId: this.currentContractId,
      currentServiceChainId: this.currentServiceChainId,
      serviceChainData : this.serviceChainData, 
    };
    return { ...super.data(), ...data };
  }


}
