.PHONY: install
install:
	sudo apt install python3-pyatspi

.PHONY: run
run:
	/usr/bin/python3 .atspi-server/main.py


.PHONY: docker
docker:
	cd .atspi-server && docker build -t atspi-server .; docker run -it atspi-server