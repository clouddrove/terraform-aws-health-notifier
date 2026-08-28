# The readme target comes from clouddrove/genie, which the readme workflow
# clones next to the workspace before running `make readme`. genie is private,
# so the include is optional: everything below works without it, and defining a
# local readme target here would shadow genie's and break that workflow.
export GENIE_PATH ?= $(shell pwd)/../../../genie
-include $(GENIE_PATH)/Makefile

.PHONY: lint fmt test tf-test package tf-validate docs

lint:
	ruff check .
	ruff format --check .
	mypy

fmt:
	ruff format .
	ruff check --fix .
	terraform fmt -recursive

test:
	pytest -v

tf-test:
	terraform test

package:
	rm -rf build dist && mkdir -p dist build
	cp -r src/handler build/handler
	cd build && zip -r ../dist/handler.zip handler -x '*.pyc' '*/__pycache__/*'

tf-validate:
	terraform fmt -check -recursive
	tflint
	checkov -d . --framework terraform --quiet


# Regenerates docs/io.md from the module's variables and outputs.
docs:
	terraform-docs markdown table --output-file docs/io.md --output-mode inject .
