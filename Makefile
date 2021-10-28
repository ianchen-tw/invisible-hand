.PHONY: clean format lint better test test-cov
ALL: test

clean:
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +

better: format lint

format:
	isort --force-single-line-imports hand

	# remove unused imports
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place hand --exclude=__init__.py

	# sort and gather imports
	isort hand

	# formatter
	black hand

format-test-src:
	isort --force-single-line-imports tests

	# remove unused imports
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place tests --exclude=__init__.py

	# sort and gather imports
	isort tests

	# formatter
	black tests

lint:
	pyflakes hand
	pyflakes tests

test:
	pytest tests -s -v

test-cov:
	# see test coverage report
	pytest --cov=hand tests