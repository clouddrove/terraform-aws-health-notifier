.PHONY: lint fmt test tf-test package tf-validate readme

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


# Regenerates README.md from README.yaml using the same genie template CI uses.
# Requires gomplate (brew install gomplate).
readme:
	@test -d /tmp/genie || git clone --depth 1 https://github.com/clouddrove/genie /tmp/genie
	@touch /tmp/readme-includes.md
	README_YAML=$(PWD)/README.yaml README_INCLUDES=/tmp/readme-includes.md \
		gomplate --file /tmp/genie/views/README.md --out README.md
	terraform-docs markdown table --output-file docs/io.md --output-mode inject .
