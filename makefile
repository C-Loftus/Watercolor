.PHONY: install
install:
	sudo apt install python3-pyatspi

.PHONY: run
run:
	/usr/bin/python3 .atspi-server/create_coords.py