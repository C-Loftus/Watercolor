import Atspi from "@girs/atspi-2.0";

function getLabel(accessible: Atspi.Accessible) {
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

function printInfo(accessible: Atspi.Accessible, appName: string | null) {
  let name;
  let roleName = "NULL";

  name = accessible.get_name();
  if (!name) name = getLabel(accessible);
  roleName = accessible.get_role_name()!;

  return "(" + name + ", " + roleName + ")";
}

function dumpNodeContent(node: Atspi.Accessible, padding: string) {
  let newPadding = padding + "  ";

  const nodeInfo = printInfo(node, node.get_name());
  print(padding + nodeInfo);

  for (let i = 0; i < node.get_child_count(); i++)
    dumpNodeContent(node.get_child_at_index(i), newPadding);
}

function dumpApplication(name: string) {
  Atspi.init();

  const desktop = Atspi.get_desktop(0);
  for (let i = 0; i < desktop.get_child_count(); i++) {
    let app = desktop.get_child_at_index(i);
    if (app.get_name() === name) {
      dumpNodeContent(app, "  ");
    }
  }
}

dumpApplication("Firefox");
