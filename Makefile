.PHONY: docs clean publish

.DEFAULT_GOAL := docs

docs: install
	poetry run jupyter-book build docs/

clean:
	poetry run jupyter-book clean --all docs/

publish: docs
	poetry run ghp-import -n -p -f docs/_build/html

install:
	poetry install
