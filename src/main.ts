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

function paintScreen(x: number, y: number) {
  console.log(`paintScreen(${x}, ${y})`);
  try {
    //  aosd_cat -n "Monospace 2
    // 8" -R "#9f9f9f" -B None -S black -f 500 -u 1000 -o 5
    const aosd_proc = Gio.Subprocess.new(
      [
        "aosd_cat",
        "--font",
        "Monospace 28",
        "-R",
        "red",
        "--back-color",
        "red",
        "--shadow-color",
        "black",
        "-u",
        "1000",
        "-o",
        "5",
        "--x-offset",
        x.toString(),
        "--y-offset",
        `-${y.toString()}`,
        "--transparency",
        "0",
      ],
      Gio.SubprocessFlags.STDIN_PIPE
    );

    const textEncoder = new TextEncoder();
    const bytes = new ByteArray.ByteArray(
      textEncoder.encode("test")
    ).toGBytes();
    console.log("fdlsajjflksasjfdkl");
    const [stdout2, stderr2] = aosd_proc.communicate(bytes, null);
    console.log("tesrsdfds");
    if (!aosd_proc.get_successful())
      throw new Error("Failed to start aosd_cat");

    // If the cancellable has already been triggered, the call to `init()` will
    // throw an error and the process will not be started.
    const cancellable = new Gio.Cancellable();

    // aosd_proc.init(cancellable);

    // Chaining to the cancellable allows you to easily kill the process. You
    // could use the same cancellabe for other related tasks allowing you to
    // cancel them all without tracking them separately.
    //
    // NOTE: this is NOT the standard GObject.connect() function, so you should
    //       consult the documentation if the usage seems odd here.
    let cancelId = 0;

    // if (cancellable instanceof Gio.Cancellable)
    //   cancelId = cancellable.connect(() => aosd_proc.force_exit());
  } catch (e) {
    logError(e);
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

    paintScreen(x, y);

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

console.log("test");

main();
