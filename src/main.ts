import Atspi from "@girs/atspi-2.0";
import Gio from "gi://Gio?version=2.0";
import GLib from "gi://GLib";

function getLabel(accessible: Atspi.Accessible) {
  const relationSet = accessible.get_relation_set();
  if (!relationSet) return null;

  for (const relation of relationSet) {
    if (relation.get_relation_type() === Atspi.RelationType.LABELLED_BY)
      return relation.get_target(0).get_name();
  }

  return null;
}

function printInfo(accessible: Atspi.Accessible) {
  let name = accessible.get_name();
  if (!name) name = getLabel(accessible);
  const roleName = accessible.get_role_name()!;

  return `(${name}, ${roleName})`;
}

function dumpNodeContent(node: Atspi.Accessible, padding: string) {
  const newPadding = padding + "  ";

  const nodeInfo = printInfo(node);

  print(padding + nodeInfo);

  for (let i = 0; i < node.get_child_count(); i++) {
    const child: Atspi.Accessible | null = node.get_child_at_index(i);

    if (!child) continue;

    const { x, y } = node.get_position(Atspi.CoordType.SCREEN);

    if (child.get_state_set().contains(Atspi.StateType.VISIBLE)) {
      dumpNodeContent(child, newPadding);

      // const textDecoder = new TextDecoder();

      // echo " -> Desktop " | aosd_cat -n "Monospace 28" -R "#9f9f9f" -B None -S black -t 2 -f 500 -u 16000 -o 500 -p 6 -l 0 -s 192 -r 255
    }
  }
}

function main() {
  Atspi.init();
  const name = ARGV[0];

  const desktop = Atspi.get_desktop(0);
  for (let i = 0, app; (app = desktop.get_child_at_index(i)); i++) {
    if (app.get_name() === name) dumpNodeContent(app, "  ");
  }
}

let echo = GLib.spawn_command_line_async('echo " -> Desktop "');
let proc = GLib.spawn_command_line_async(
  'echo " -> Desktop " | aosd_cat -n "Monospace 28" -R "#9f9f9f" -B None -S black -t 2 -f 500 -u 16000 -o 500 -p 6 -l 0 -s 192 -r 255'
);
// main();
