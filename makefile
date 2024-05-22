.PHONY: install
install:
	sudo apt install python3-pyatspi

.PHONY: run
run:
	/usr/bin/python3 .atspi-server/main.py


.PHONY: docker
docker:
	cd .atspi-server && docker build -t atspi-server .; docker run -it atspi-server


.PHONY: test
test: dev
	/usr/bin/python3 -m pytest tests/test_lib.py

dev:
	/usr/bin/python3 -m pip install pytest