.PHONY: lint fmt test package plan tf-validate

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

package:
	rm -rf build dist && mkdir -p dist build
	cp -r src/handler build/handler
	cd build && zip -r ../dist/handler.zip handler -x '*.pyc' '*/__pycache__/*'

tf-validate:
	terraform fmt -check -recursive
	tflint
	checkov -d . --framework terraform --quiet

plan:
	terraform -chdir=deploy plan
