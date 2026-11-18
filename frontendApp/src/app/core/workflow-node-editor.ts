import { Injector } from "@angular/core";
import { BaseSchemes, NodeEditor, Root } from "rete";
import { WorkflowEditor } from "./workflow-editor";


interface NodeDataOutputUpdated<Scheme extends BaseSchemes> {
  type: 'nodeDataOutputUpdated';
  data: {
    nodeId: string,
    outputKey: string,
  }
}

export type CustomRoot<Scheme extends BaseSchemes> = Root<Scheme> | NodeDataOutputUpdated<Scheme>;

export class WorkflowNodeEditor<Scheme extends BaseSchemes> extends NodeEditor<Scheme> {
  constructor(public injector: Injector,public core :WorkflowEditor) {
    super();
  }
  override emit<C extends CustomRoot<Scheme>>(context: C):Promise<Extract<CustomRoot<Scheme>, C> | undefined> {
    return super.emit(context as any) as Promise<Extract<CustomRoot<Scheme>, C> | undefined>;
  }
}
