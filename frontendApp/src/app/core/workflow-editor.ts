import { Node } from 'src/app/models/interfaces/node';
import { Preset } from 'rete-dock-plugin/_types/presets/types';
import { NodeConnection } from '../models/interfaces/node-connection';
import { ClassicPreset, GetSchemes } from 'rete';

import { NodePort } from '../models/interfaces/node-port';
import { NodeControl } from '../models/interfaces/node-control';
import { WorkflowNodeEditor } from './workflow-node-editor';
import { Schema } from '../models/interfaces/schema';
import { Project } from '../models/interfaces/project';
import {
  AngularArea2D,
  AngularPlugin,
  ConnectionComponent,
  ControlComponent,
  NodeComponent,
  Presets,
  SocketComponent,
} from 'rete-angular-plugin/19';
import {
  ClassicFlow,
  ConnectionPlugin,
  getSourceTarget,
} from 'rete-connection-plugin';
import { AreaExtensions, AreaPlugin } from 'rete-area-plugin';
import { Injector } from '@angular/core';
import { DockPlugin, DockPresets } from 'rete-dock-plugin';
import { DataLrsBlock } from '../nodes/inputs/data-lrs-block';
import { DataMongoBlock } from '../nodes/inputs/data-mongo-block';
import { NodeBlock, registeredBlock } from '../nodes/node-block';
import { DataFileBlock } from '../nodes/inputs/data-file-block';
import { DataMysqlBlock } from '../nodes/inputs/data-mysql-block';
import { DataElasticBlock } from '../nodes/inputs/data-elastic-block';
import {
  FlatObjectSocket,
  LrsObjectSocket,
  SimpleFieldSocket,
  getConnectionSockets,
  BaseSocket,
  DeepObjectSocket,
  Sockets,
  AllSocket,
} from './sockets/sockets';
import '../nodes';
import {
  StatusComponentComponent,
  StatusControl,
} from '../components/widgets/status-component/status-component.component';
import { Presets as ArrangePresets,AutoArrangePlugin } from 'rete-auto-arrange-plugin';
import { ContextMenuExtra, ContextMenuPlugin,Presets as ContextMenuPresets } from 'rete-context-menu-plugin';
import { DataMapperControl, DataMapperWidgetComponent } from '../components/widgets/data-mapper-widget/data-mapper-widget.component';
import { SelectControl, SelectWidgetComponent } from '../components/widgets/select-widget/select-widget.component';
import { NodeLoaderControl, NodeLoaderWidgetComponent } from '../components/widgets/node-loader-widget/node-loader-widget.component';
import { CustomDockPresets } from './presets/CustomDock';
import { ButtonControl, ButtonWidgetComponent } from '../components/widgets/button-widget/button-widget.component';
import { WorkflowService } from '../services/worflow.service';
import { InputAutoCompleteControl, InputAutoCompleteWidgetComponent } from '../components/widgets/auto-complete-widget/input-auto-complete-widget.component';
import { StatusNode } from '../enums/status-node';
import { NodeData } from '../models/node-data';
import { CheckboxControl, CheckboxWidgetComponent } from '../components/widgets/checkbox-widget/checkbox-widget.component';
import { ContextMenuDaavPlugin, setup } from './contextMenuDaav';
import { DataFilterControl, DataFilterWidgetComponent } from '../components/widgets/data-filter-widget/data-filter-widget.component';
import { JsonInputsControl, JsonInputsWidgetComponent } from '../components/widgets/json-inputs-widget/json-inputs-widget.component';
import { TextDisplayControl, TextDisplayWidgetComponent } from '../components/widgets/text-display-widget/text-display-widget.component';


class Connection<N extends NodeBlock> extends ClassicPreset.Connection<N, N> {}

export type Schemes = GetSchemes<NodeBlock, Connection<NodeBlock>>;

export type AreaExtra = AngularArea2D<Schemes>| ContextMenuExtra;

type Nodes =
  | NodeBlock
  | DataLrsBlock
  | DataMongoBlock
  | DataFileBlock
  | DataMysqlBlock
  | DataElasticBlock;

export class WorkflowEditor {
  project: Project;
  nodeEditor: WorkflowNodeEditor<Schemes>;

  connection: ConnectionPlugin<Schemes, AreaExtra>;
  id: string;
  name: string;
  revision : string;
  area: AreaPlugin<Schemes, AreaExtra>;
  render: AngularPlugin<Schemes, AreaExtra>;
  dock: DockPlugin<Schemes>;
  injector: Injector;
  arrange: AutoArrangePlugin<Schemes, never>;
  contextMenu: ContextMenuPlugin<Schemes>;

  constructor(container: HTMLElement, injector: Injector) {
    this.injector = injector;
    this.nodeEditor = new WorkflowNodeEditor<Schemes>(injector, this);
    this.area = new AreaPlugin<Schemes, AreaExtra>(container);
    this.connection = new ConnectionPlugin<Schemes, AreaExtra>();
    this.connectionRule();
    this.render = new AngularPlugin<Schemes, AreaExtra>({ injector });
    this.customRender();
    this.arrange = new AutoArrangePlugin<Schemes>();

    this.arrange.addPreset(ArrangePresets.classic.setup());


    AreaExtensions.selectableNodes(this.area, AreaExtensions.selector(), {
      accumulating: AreaExtensions.accumulateOnCtrl(),
    });
    this.dock = new DockPlugin<Schemes>();
    this.dock.addPreset(
      CustomDockPresets.setup({ area: this.area, size: 100, scale: 0.4 })
    );

    const  items = this.buildContextMenu();
    this.contextMenu = new ContextMenuDaavPlugin<Schemes>({
      items: setup(items),
    });
    this.area.use(this.contextMenu).debug($ => $);

    this.nodeEditor.use(this.area);
    this.area.use(this.connection);
    this.area.use(this.render);
    this.area.use(this.dock);
    this.area.use(this.arrange);
    this.buildDockContent();
    AreaExtensions.simpleNodesOrder(this.area);
    AreaExtensions.zoomAt(this.area, this.nodeEditor.getNodes());
    AreaExtensions.showInputControl(this.area);
    console.log(registeredBlock);
  }

  buildContextMenu() {
    // Group nodes by their type
    const nodesByType = new Map<string, Array<{name: string, blockClass: any}>>();

    registeredBlock.forEach((block,key) => {
      const blockClass = block.class as any;
      if (!nodesByType.has(block.type)) {
        nodesByType.set(block.type, []);
      }
      nodesByType.get(block.type).push({
        name: key,
        blockClass
      });
    });

    // Convert the map to the required format for context menu
    const menuItems = Array.from(nodesByType.entries()).map(([type, blocks]) => {
      // If only one block of this type, create a direct menu item
      if (blocks.length === 1) {
        const block = blocks[0];
        return [block.name, () => new block.blockClass(block.name, this.area)] as [string, () => any];
      }

      // Otherwise, create a submenu with all blocks of this type
      const submenu = blocks.map(block => {
        return [block.name, () => new block.blockClass(block.name, this.area)] as [string, () => any];
      });

      return [type, submenu] as [string, [string, () => any][]];
    });

    return menuItems;
  }

  private connectionRule() {
    //this.connection.addPreset(() => new ClassicFlow());
    this.nodeEditor.addPipe((context) => {
      if (context.type === 'connectioncreate') {
        const { data } = context;
        const { source, target } = getConnectionSockets(this.nodeEditor, data);

        if (!source.isCompatibleWith(target)) {
          console.log('Sockets are not compatible', 'error');
          return null;
        }
      }
      return context;
    });
    this.connection.addPreset(
      () =>
        new ClassicFlow({
          canMakeConnection: (from, to) => {
            // this function checks if the old connection should be removed
            const [source, target] = getSourceTarget(from, to) || [null, null];

            if (!source || !target || from === to) return false;

            const sockets = getConnectionSockets(
              this.nodeEditor,
              new ClassicPreset.Connection<
                ClassicPreset.Node,
                ClassicPreset.Node
              >(
                this.nodeEditor.getNode(source.nodeId),
                source.key as never,
                this.nodeEditor.getNode(target.nodeId),
                target.key as never
              )
            );
            console.log(sockets);

            if (!sockets.source.isCompatibleWith(sockets.target)) {
              console.log('Sockets are not compatible', 'error');
              this.connection.drop();
              return false;
            }

            return Boolean(source && target);
          },
          makeConnection(from, to, context) {
            const [source, target] = getSourceTarget(from, to) || [null, null];
            const { editor } = context;

            if (source && target) {
              editor.addConnection(
                new ClassicPreset.Connection<
                  ClassicPreset.Node,
                  ClassicPreset.Node
                >(
                  editor.getNode(source.nodeId),
                  source.key as never,
                  editor.getNode(target.nodeId),
                  target.key as never
                )
              );
              return true;
            } else return false;
          },
        })
    );
  }

  private customRender() {
    this.render.addPreset(
      Presets.classic.setup({
        customize: {
          connection: (data) => {
            const { source, target } = getConnectionSockets(
              this.nodeEditor,
              data.payload
            );
            const port = source ? source : target;
            if (port) {
              return port?.getConnectionComponent();
            } else {
              return ConnectionComponent;
            }
          },
          socket: (data) => {
            if (data.payload instanceof BaseSocket) {
              return data.payload.getSocketComponent();
            }
            return SocketComponent;
          },
          node: (data) => {
            if (data.payload instanceof NodeBlock) {
              return data.payload.getNodeComponent();
            }
            return NodeComponent;
          },
          control(data) {
            if (data.payload instanceof TextDisplayControl) {
              return TextDisplayWidgetComponent;
            }
            if (data.payload instanceof JsonInputsControl) {
              return JsonInputsWidgetComponent;
            }
            if (data.payload instanceof SelectControl) {
              return SelectWidgetComponent;
            }
            if (data.payload instanceof ButtonControl) {
              return ButtonWidgetComponent;
            }
            if (data.payload instanceof NodeLoaderControl) {
              return NodeLoaderWidgetComponent;
            }
            if (data.payload instanceof StatusControl) {
              return StatusComponentComponent;
            }
            if (data.payload instanceof DataMapperControl){
              return DataMapperWidgetComponent;
            }
            if (data.payload instanceof DataFilterControl){
              return DataFilterWidgetComponent;
            }
            if (data.payload instanceof ClassicPreset.InputControl) {
              return ControlComponent;
            }
            if (data.payload instanceof InputAutoCompleteControl) {
              return InputAutoCompleteWidgetComponent;
            }
            if (data.payload instanceof CheckboxControl) {
              return CheckboxWidgetComponent;
            }
            return null;
          },
        },
      })
    );
   this.render.addPreset(Presets.contextMenu.setup({'delay':50}));
  }

  async resetWorkflow(projectName? : string){
    this.id = null;
    this.project = null;
    this.name = projectName || '';
    this.project = null;
    this.revision = null;
    await this.nodeEditor.clear();
  }

  async importProject(project: Project) {
    this.project = project;
    this.id = project.id;
    this.name = project.name;
    await this.nodeEditor.clear();
    for (const nodeI of this.project.schema.nodes) {
      let node: NodeBlock;
      let buildContent = false;
      //Factory to instantiate the daav node block by her type from a list of registered class tagged with a decorator
      if (registeredBlock.has(nodeI.type)) {
        node = new (registeredBlock.get(nodeI.type).class as any)(
          nodeI.label,
          this.area,
          nodeI
        );
        node.id = nodeI.id;
        if (node instanceof NodeBlock) {
          buildContent = !node.rebuildLocally;
        }
        //deactivate node event who can fire reactive input creation
        node.preventNodeEvent = true;
        console.log("activate prevent default "+node);
      } else {
        throw new Error("this type : {nodeI.type} of block can't be found ");
      }
      //if NodeBlock recreation of node content can be delegate at the object constructor or handle here if rebuild Locally is false or it's a classic preset
      if (buildContent) {
        Object.entries(nodeI.inputs).forEach(([key, input]: [string, any]) => {
          const socket = this.socketFactory(input.socket.name);
          const inp = new ClassicPreset.Input(socket, input.label);

          inp.id = input.id;

          node.addInput(key, inp);
        });
        Object.entries(nodeI.outputs).forEach(
          ([key, output]: [string, any]) => {
            const socket = this.socketFactory(output.socket.name);
            const out = new ClassicPreset.Output(socket, output.label);

            out.id = output.id;

            node.addOutput(key, out);
          }
        );
        Object.entries<ReturnType<typeof this.serializeControl>>(
          nodeI.controls
        ).forEach(([key, control]) => {
          if (!control) return;

          if (control.__type === 'ClassicPreset.InputControl') {
            const ctrl = new ClassicPreset.InputControl(control.type, {
              initial: control.value,
              readonly: control.readonly,
            });
            node.addControl(key, ctrl);
          }
        });
      }

      await this.nodeEditor.addNode(node);
      if (nodeI.position){
        await this.area.translate(node.id, nodeI.position);
      }
    }
    await Promise.all(this.project.schema.connections.map(async (connection) => {
      const connectionObject = new ClassicPreset.Connection(
        this.nodeEditor.getNode(connection.sourceNode),
        connection.sourcePort,
        this.nodeEditor.getNode(connection.targetNode),
        connection.targetPort
      );
      connectionObject.id = connection.id;
      await this.nodeEditor.addConnection(connectionObject);
      console.log("add connection ");
    }));
    //reactivate node event
    this.nodeEditor.getNodes().forEach((node) => {
      node.preventNodeEvent = false;
      console.log("desactivate prevent default "+node);
    });
    //await this.arrange.layout({options : {}});
    AreaExtensions.zoomAt(this.area, this.nodeEditor.getNodes());
  }
  /**
   *
   * @returns Export DaavProject
   */
  exportProject(): Project {
    const schemaDaav: Schema = { nodes: [], connections: [],revision:null };

    //TODO add dataconnector
    const projectDaav: Project = {
      schema: schemaDaav,
      dataConnectors: [],
      id: this.id,
      name: this.name,
      revision: this.revision
    };
    const nodes = this.nodeEditor.getNodes();
    let data: any;


    for (const node of nodes) {
      const inputsEntries = Object.entries(node.inputs).map(([key, input]) => {
        return [key, input && this.serializePort(input)];
      });
      const outputsEntries = Object.entries(node.outputs).map(
        ([key, output]) => {
          return [key, output && this.serializePort(output)];
        }
      );
      const controlsEntries = Object.entries(node.controls).map(
        ([key, control]) => {
          return [key, control && this.serializeControl(control)];
        }
      );
      if (node instanceof NodeBlock) {
        data = node.data();
      }
      //reset status Error to complete node on Error can't be executed on server but have been at complete state before
      if (data.status === StatusNode.Error){
        data.status= StatusNode.Complete;
        data.statusMessage = null;
        data.errorStacktrace = [];
      }
      //TODO call revision for DaavNode
      projectDaav.schema.nodes.push({
        id: node.id,
        type: node.constructor.name,
        label: node.label,
        revision: '',
        data,
        outputs: Object.fromEntries(outputsEntries),
        inputs: Object.fromEntries(inputsEntries),
        controls: Object.fromEntries(controlsEntries),
        position: this.area.nodeViews.get(node.id).position,
      });
      //TODO save connections beetween node
    }

    const addConnection: NodeConnection[] = [];
    this.nodeEditor.getConnections().forEach((connection) => {
      const connectionData = {
        id: connection.id,
        sourceNode: connection.source,
        targetNode: connection.target,
        sourcePort: connection.sourceOutput,
        targetPort: connection.targetInput,
      };
      addConnection.push(connectionData);
    });
    projectDaav.schema.connections = addConnection;

    return projectDaav;
  }

  /**
   * Export and Save project on backend
   */
  saveProject() {
    this.project = this.exportProject();
    //TODO push to server
  }

  private buildDockContent() {
    //TODO scan plugin directory to add programamtically all node class to the toolbar
    registeredBlock.forEach((block) => {
      let blockClass = block.class as any;
      this.dock.add(() => new blockClass(blockClass.name, this.area));
      this.dock.addPipe
    });
  }

  private

  private serializePort(
    port:
      | ClassicPreset.Input<ClassicPreset.Socket>
      | ClassicPreset.Output<ClassicPreset.Socket>
  ): NodePort {
    return {
      id: port.id,
      label: port.label,
      socket: {
        name: port.socket.name,
      },
    };
  }

  private serializeControl(control: ClassicPreset.Control): NodeControl | null {
    if (control instanceof ClassicPreset.InputControl) {
      return {
        __type: 'ClassicPreset.InputControl' as const,
        id: control.id,
        readonly: control.readonly,
        type: control.type,
        value: control.value,
      };
    }
    return null;
  }

  private socketFactory(type: string): Sockets | ClassicPreset.Socket {
    let socket: Sockets | ClassicPreset.Socket;
    switch (type) {
      case 'SimpleFieldSocket':
        socket = new SimpleFieldSocket();
        break;
      case 'LrsObjectSocket':
        socket = new LrsObjectSocket();
        break;
      case 'DeepObjectSocket':
        socket = new DeepObjectSocket();
        break;
      case 'FlatObjectSocket':
        socket = new FlatObjectSocket();
        break;
      case 'AllSocket':
        socket = new AllSocket();
        break;
      default:
        socket = new ClassicPreset.Socket(type);
        break;
    }
    return socket;
  }

  executeNodeJson(nodeId ?: string) {
    this.injector.get(WorkflowService).executeNodeJson(this.exportProject(),nodeId).subscribe((project) => {
      this.updateProjectStatus(project);
    });
  }

  updateProjectStatus(project : Project) {
    project.schema.nodes.forEach((node) => {
        const currentNode = this.nodeEditor.getNode(node.id);

        // Process node response first
        currentNode.processNodeResponse(node);

        currentNode.updateStatus(node.data.status, node.data.statusMessage, node.data.errorStacktrace);
        const previousDataOutput = this.nodeEditor.getNode(node.id).dataOutput;
        const newDataOutput = new Map<string,NodeData<any>>(Object.entries(node.data.dataOutput));

        if (newDataOutput.size > 0 || currentNode.status === StatusNode.Error) {
          this.nodeEditor.getNode(node.id).dataOutput = newDataOutput;
        }
        newDataOutput.forEach((value, key) => {
          if (!previousDataOutput || !previousDataOutput.get(key) ||previousDataOutput.get(key).dataExample !== value.dataExample) {
            this.nodeEditor.emit({
              type: "nodeDataOutputUpdated",
              data: {
                  nodeId: node.id,
                  outputKey: key,
              }
            });
          this.nodeEditor.getNode(node.id).outputs[key].id
          }
        });
    });
  }

}
