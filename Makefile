.PHONY: remake

PACKAGENAME = voice_lock
LOG = ./$(PACKAGENAME)/log/pylint

all: ui

ui:
	python3 setup.py build_ui

run:
	python3 -m $(PACKAGENAME)


remake: all run

pylint: clean_log
	touch $(LOG)
	pylint $(PACKAGENAME) > $(LOG)
	vim $(LOG)

clean_log:
	rm -f $(LOG)
