import Atspi from "@girs/atspi-2.0";
import Gio from "gi://Gio?version=2.0";
import GLib from "gi://GLib";
import test from "node:test";
const ByteArray = imports.byteArray;

function getLabel(accessible: Atspi.Accessible) {
  const relationSet = accessible.get_relation_set();
  if (!relationSet) return null;

  for (const relation of relationSet) {
    if (relation.get_relation_type() === Atspi.RelationType.LABELLED_BY)
      return relation.get_target(0).get_name();
  }

  return null;
}
Gio._promisify(
  Gio.Subprocess.prototype,
  "communicate_utf8_async",
  "communicate_utf8_finish"
);
async function paintScreen(x: number, y: number) {
  console.log(`paintScreen(${x}, ${y})`);
  const aosd_cmd = [
    "aosd_cat",
    "--font",
    "Ubuntu Mono 20",
    "--fore-color",
    "#89c1a5",
    "--back-color",
    "#9cb0c3",
    "--shadow-color",
    "black",
    "--fade-full",
    "1000", //seconds
    "--back-opacity",
    "90", //%
    "--padding",
    "5", //px
    "--fade-out",
    "3", //seconds
    "--x-offset",
    x.toString(),
    "--y-offset",
    `-${y.toString()}`,
    "--transparency",
    "1", // 1 = fake compositing
  ];

  try {
    const cancelHandle = Gio.Cancellable.new();
    const proc = Gio.Subprocess.new(aosd_cmd, Gio.SubprocessFlags.STDIN_PIPE);
    await proc.communicate_utf8_async("LABEL_NAME", cancelHandle);
  } catch (e) {
    console.error(e);
  }
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

    if (child.get_state_set().contains(Atspi.StateType.FOCUSABLE)) {
      paintScreen(x, y);
    }

    if (child.get_state_set().contains(Atspi.StateType.VISIBLE)) {
      dumpNodeContent(child, newPadding);
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

main();
