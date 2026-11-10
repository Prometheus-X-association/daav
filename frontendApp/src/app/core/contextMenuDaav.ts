import { BaseSchemes, NodeEditor, Scope } from 'rete';
import { ContextMenuPlugin, Props } from 'rete-context-menu-plugin';
import { BaseAreaPlugin } from 'rete-area-plugin';
import _typeof from '@babel/runtime/helpers/typeof';
import _getPrototypeOf from '@babel/runtime/helpers/getPrototypeOf';
import _get from '@babel/runtime/helpers/get';
import { Item, Items, Position } from 'rete-context-menu-plugin/_types/types';
import { BSchemes, ItemDefinition } from 'rete-context-menu-plugin/_types/presets/classic/types';
import { NodeBlock } from '../nodes';

export class ContextMenuDaavPlugin<
  Schemes extends BaseSchemes
> extends ContextMenuPlugin<Schemes> {
  eprops: Props<Schemes>;
  constructor(props: Props<Schemes>) {
    super(props);
    this.eprops = props;
  }

  override setParent(
    scope: Scope<
      | { type: 'unmount'; data: { element: HTMLElement } }
      | {
          type: 'pointerdown';
          data: { position: Position; event: PointerEvent };
        }
      | {
          type: 'contextmenu';
          data: {
            event: MouseEvent;
            context: 'root' | Schemes['Node'] | Schemes['Connection'];
          };
        },
      []
    >
  ): void {
    //super.setParent(scope);
    _superPropGet(ContextMenuPlugin, 'setParent', this, 3)([scope]);
    let parentScope = this.parentScope(BaseAreaPlugin);
    var container = (parentScope as any).container as HTMLElement;
    var element = document.createElement('div');
    element.style.display = 'none';
    element.style.position = 'fixed';

    this.addPipe((context) => {
      var parent = parentScope;
      if (!context || _typeof(context) !== 'object' || !('type' in context))
        return context;
      if (context.type === 'unmount') {
        if (context.data.element === element) {
          element.style.display = 'none';
        }
      } else if (context.type === 'contextmenu') {
        context.data.event.preventDefault();
        context.data.event.stopPropagation();
        var _this2$props$items = this.eprops.items(context.data.context, this),
          searchBar = _this2$props$items.searchBar,
          list = _this2$props$items.list;
        container.appendChild(element);
        let parentContainerTarget = ((context.data.event.currentTarget) as any).parentElement.parentElement as HTMLElement;
        element.style.left = ''.concat(
          (context.data.event.pageX - parentContainerTarget.getBoundingClientRect().left).toString(),
          'px'
        );
        element.style.top = ''.concat(
          context.data.event.clientY.toString(),
          'px'
        );
        element.style.display = '';
        void parent.emit({
          type: 'render',
          data: {
            type: 'contextmenu',
            element: element,
            searchBar: searchBar,
            onHide: function onHide() {
              void parent.emit({
                type: 'unmount',
                data: {
                  element: element,
                },
              });
            },
            items: list,
          },
        });
      } else if (context.type === 'pointerdown') {
        if (!context.data.event.composedPath().includes(element)) {
          void parent.emit({
            type: 'unmount',
            data: {
              element: element,
            },
          });
        }
      }
      return context;
    });
  }
}

function _superPropGet(t, e, o, r) {
  var p = _get(_getPrototypeOf(1 & r ? t.prototype : t), e, o);
  return 2 & r && 'function' == typeof p
    ? function (t) {
        return p.apply(o, t);
      }
    : p;
}

export function setup<Schemes extends BSchemes>(nodes: ItemDefinition<Schemes>[]) {
  return function (context, plugin) {
    const area = plugin.parentScope<BaseAreaPlugin<Schemes, any>>(BaseAreaPlugin)
    const editor = area.parentScope<NodeEditor<Schemes>>(NodeEditor)

    if (context === 'root') {
      return {
        searchBar: false,
        list: nodes.map((item, i) => createItem(item, i, { editor, area }))
      }
    }

    const deleteItem: Item = {
      label: 'Delete',
      key: 'delete',
      async handler() {

        if ('source' in context && 'target' in context) {
          // connection
          const connectionId = context.id

          await editor.removeConnection(connectionId)
        } else {
          // node

          const nodeId = context.id
          const node = editor.getNode(nodeId) as NodeBlock
          node.preventNodeEvent = true;
          const connections = editor.getConnections().filter(c => {
            return c.source === nodeId || c.target === nodeId
          })

          for (const connection of connections) {
            await editor.removeConnection(connection.id)
          }
          await editor.removeNode(nodeId)
        }
      }
    }

    const clone = context.clone?.bind(context)
    const cloneItem: undefined | Item = clone && {
      label: 'Clone',
      key: 'clone',
      async handler() {
        const node = clone()

        await editor.addNode(node)

        void area.translate(node.id, area.area.pointer)
      }
    }

    return {
      searchBar: false,
      list: [
        deleteItem,
        ...cloneItem
          ? [cloneItem]
          : []
      ]
    }
  } satisfies Items<Schemes>
}

export function createItem<S extends BSchemes>(
  [label, factory]: ItemDefinition<S>,
  key: string | number,
  context: { editor: NodeEditor<S>, area: BaseAreaPlugin<S, any> }
): Item {
  const item: Item = {
    label,
    key: String(key),
    handler() {
      /* noop */
    }
  }

  if (typeof factory === 'function') {
    return {
      ...item,
      async handler() {
        const node = await factory()

        await context.editor.addNode(node)

        void context.area.translate(node.id, context.area.area.pointer)
      }
    } satisfies Item
  }
  return {
    ...item,
    handler() { /* do nothing */ },
    subitems: factory.map((data, i) => createItem(data, i, context))
  } satisfies Item
}
