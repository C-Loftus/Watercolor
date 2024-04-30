/*
 * Usage:
 *    gjs dump-tree <application-name>
 *
 * Dump the accessibility hiearchy tree for a given application.
 */

const Atspi = imports.gi.Atspi;
const GLib = imports.gi.GLib;

function getLabel(accessible) {
  let relationSet;
  let i = 0;

  relationSet = accessible.get_relation_set();
  if (!relationSet) return "NULL";

  /* something like "let relation in relationSet" doesn't work, and
   * it seems that GArray "len" is not exposed */
  while (relationSet[i]) {
    let relation = relationSet[i];

    if (relation.get_relation_type() == Atspi.RelationType.LABELLED_BY)
      return relation.get_target(0).get_name();

    i++;
  }

  return "NULL";
}

function printInfo(accessible, appName) {
  let name;
  let roleName = "NULL";
  let stateSetString = "NULL";

  name = accessible.get_name();
  if (!name) name = getLabel(accessible);
  roleName = accessible.get_role_name();

  return "(" + name + ", " + roleName + ")";
}

function dumpNodeContent(node, padding) {
  let newPadding = padding + "  ";

  nodeInfo = printInfo(node);
  print(padding + nodeInfo);

  for (let i = 0; i < node.get_child_count(); i++)
    dumpNodeContent(node.get_child_at_index(i), newPadding);
  let coord = node.get_position(Atspi.CoordType.ATSPI_COORD_TYPE_SCREEN);
  print(coord.x);
  print(coord.y);
}

function dumpApplication(appName) {
  let desktop;
  let found = false;

  Atspi.init();

  desktop = Atspi.get_desktop(0);
  for (let i = 0; i < desktop.get_child_count(); i++) {
    let app = desktop.get_child_at_index(i);
    if (app.get_name() == appName) {
      found = true;
      dumpNodeContent(app, "  ");
    }
  }

  if (!found) {
    print("ERROR: Application " + appName + " not found");
  }
}

// Define the command you want to execute
let command = "./cat.sh";

try {
  GLib.spawn_command_line_sync(command);
} catch (err) {
  print("ERROR: " + err);
}

// atspi_state_set_get_states method
//     Returns the states in an #AtspiStateSet as an array.
// atspi_accessible_get_state_set method
//     Gets the states currently held by an object.

// name watercolor