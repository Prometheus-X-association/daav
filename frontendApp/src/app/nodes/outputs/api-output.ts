import { AreaPlugin } from "rete-area-plugin";
import { daavBlock } from "../node-block";
import { OutputDataBlock } from "../output/output-data-block";
import { AreaExtra, Schemes } from "src/app/core/workflow-editor";
import { Node } from 'src/app/models/interfaces/node';
import { StatusNode } from "src/app/enums/status-node";
import { ClassicPreset } from "rete";
import { AllSocket } from "src/app/core/sockets/sockets";
import { InputAutoCompleteControl, InputAutoCompleteControlI } from "src/app/components/widgets/auto-complete-widget/input-auto-complete-widget.component";
import { MatAutocompleteSelectedEvent } from "@angular/material/autocomplete";
import { WorkflowNodeEditor } from "src/app/core/workflow-node-editor";
import { MatSelectChange } from "@angular/material/select";

@daavBlock("output")
export class ApiOutput extends OutputDataBlock{
  override width = 500;
  private readonly node: Node;

  private nameControl: InputAutoCompleteControl;
  private urlControl: InputAutoCompleteControl;
  private tokenControl: InputAutoCompleteControl;

  constructor(
    label: string,
    area: AreaPlugin<Schemes, AreaExtra>,
    node?: Node
  ){
    super(label, area, node);
    this.worflowEditor = this.area.parent as WorkflowNodeEditor<Schemes>;
    this.node = node;


    if(!node) {
      this.status = StatusNode.Incomplete;
      this.addInput(
        'in',
        new ClassicPreset.Input(new AllSocket(), "In")
      )
    }

    this.addNameInput(node);
    this.addUrlInput(node);
    this.addTokenInput(node);

    this.validateInput();
    this.area.update("node", this.id);
  }

  override addSourceSelect(){
    // No data source select: the API output is configured by its URL.
  }

  private generateRandomToken(length: number = 64): string {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    const charactersLength = characters.length;
    for (let i = 0; i < length; i++) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
  }

  dataBaseChange(event: MatSelectChange) {
    console.log('database source change', event);
  }

  private addTokenInput(node: Node): void{
    let tokenInput: InputAutoCompleteControlI;
    if(node?.data?.tokenInput){
        tokenInput = node.data.tokenInput
    }else {
        tokenInput = {
        value: this.generateRandomToken(),
        list: [],
        label: 'Enter the token',
        type: 'password',
        showPassword: false,
      };
    }

    this.tokenControl = new InputAutoCompleteControl(
        tokenInput,
        (event) => {
          if(event instanceof InputEvent && (event.target as HTMLInputElement).value ||
             event instanceof MatAutocompleteSelectedEvent && event.option.value){
              this.validateInput();
             }
          else {
            this.updateStatus(StatusNode.Incomplete);
          }
        }
      )
      this.addControl('token', this.tokenControl);
      this.area.update('control', this.tokenControl.id);
      this.area.update('node', this.id);
}

  private addNameInput(node: Node): void{
    let nameInput: InputAutoCompleteControlI;
    if(node?.data?.nameInput){
      nameInput = node.data.nameInput
    }else {
      nameInput = {
        value: '',
        list: [],
        label: 'Name',
        type: 'text',
      };
    }

    this.nameControl = new InputAutoCompleteControl(
      nameInput,
      (event) => {
        if(event instanceof InputEvent && (event.target as HTMLInputElement).value ||
           event instanceof MatAutocompleteSelectedEvent && event.option.value){
            this.validateInput();
           }
        else {
          this.updateStatus(StatusNode.Incomplete);
        }
      }
    )
    this.addControl('name', this.nameControl);
    this.area.update('control', this.nameControl.id);
    this.area.update('node', this.id);
  }

  private addUrlInput(node: Node): void{
    let urlInput: InputAutoCompleteControlI;
    if(node?.data?.urlInput){
      urlInput = node.data.urlInput
    }else {
      urlInput = {
        value: '',
        list: [],
        label: 'URL',
        type: 'url',
      };
    }

    this.urlControl = new InputAutoCompleteControl(
      urlInput,
      (event) => {
        if(event instanceof InputEvent && (event.target as HTMLInputElement).value ||
           event instanceof MatAutocompleteSelectedEvent && event.option.value){
              this.validateInput();
           }
        else {
          this.updateStatus(StatusNode.Incomplete);
        }
      }
    )
    this.addControl('url', this.urlControl);
    this.area.update('control', this.urlControl.id);
    this.area.update('node', this.id);
  }

  private extractValue(event: InputEvent | MatAutocompleteSelectedEvent): string {
    if (event instanceof InputEvent) {
      return (event.target as HTMLInputElement)?.value || '';
    }
    return event.option?.value || '';
  }

  private validateInput(){
    const nameValue = this.nameControl?.value;
    const urlValue = this.urlControl?.value;

    if(!nameValue && !urlValue){
      this.updateStatus(StatusNode.Incomplete, "Name and url fields are required");
      return;
    }

    if (!nameValue) {
      this.updateStatus(StatusNode.Incomplete, "Name is required");
      return;
    }

    if (!urlValue) {
      this.updateStatus(StatusNode.Incomplete, "URL is required");
      return;
    }

    const isValidUrl = /^[a-zA-Z0-9_/-]+$/.test(urlValue);
    if (!isValidUrl) {
      this.updateStatus(StatusNode.Incomplete, "Invalid URL format");
      return;
    }

    this.updateStatus(StatusNode.Complete);
    this.area.update('node', this.id);
  }



  override data(){
    const data = {
      nameInput: this.nameControl,
      urlInput: this.urlControl,
      tokenInput: this.tokenControl,
    }
    return { ...super.data(), ...data };
  }
}
