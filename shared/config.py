# Used by the client to connect to the server which sends the focus or click events
SOCKET_PATH = "/tmp/watercolor-at-spi-server.sock"

# Talon can resource watch the tree easier than polling a socket, so we'll use that
TREE_OUTPUT_PATH = '/tmp/a11y_tree.json'