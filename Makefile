.ONESHELL:

U_NAME := $(shell uname -s)

all:
	pip3 install virtualenv --user
	python3 -m virtualenv protractor_gen_build
	. ./protractor_gen_build/bin/activate
	make install-reqs
	@if [ "$(U_NAME)" = "Darwin" ]; then \
		PYINSTALLER_FLAG="--onedir"; \
	else \
		PYINSTALLER_FLAG="--onefile"; \
	fi
	python3 -m PyInstaller --clean --name="TempSim" $$PYINSTALLER_FLAG --windowed --icon=icon/icon.png main.pyw
	make clean-up


install-reqs:
	pip3 install -r requirements.txt --user

build-ui:
	pyuic5 -x protractor_ui.ui -o protractor_ui.py
	pyuic5 -x about_ui.ui -o about_ui.py

clean-up:
	rm -rf protractor_gen_build
	rm -rf __pycache__

clean:
	make clean-up
	rm -rf build
	rm -rf dist