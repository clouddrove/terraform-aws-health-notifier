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


readme:
	docker run --rm -v "$(PWD):/data" cytopia/terraform-docs terraform-docs-replace-012 md README.md
