all : install prep-container

.PHONY: install prep-container

prep-container:
	sudo install ./container-opentts.service /etc/systemd/system/
	sudo podman pull 'docker.io/synesthesiam/opentts@sha256:9b9dbd4b4a54ad21f56b058925327d7db51496e2d4afd5683d1920dbb708a119'
	sudo systemctl daemon-reload
	sudo systemctl enable container-opentts
	sudo systemctl start container-opentts

install:
	python -m pip install -e .
	ln -sfv $(shell which maggieCtrl) /opt/MagAOX/bin/maggieCtrl