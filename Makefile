PYTHON ?= python

all: bdist_egg

bdist_egg:
	$(PYTHON) setup.py $@

pypi_upload:
	$(PYTHON) setup.py sdist upload -r pypi --sign

pypi_register:
	$(PYTHON) setup.py sdist register -r pypi
