.PHONY: clean format lint better test test-cov
ALL: test

clean:
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +

better: lint format

format:
	isort --force-single-line-imports invisible_hand

	# remove unused imports
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place invisible_hand --exclude=__init__.py

	# sort and gather imports
	isort invisible_hand

	# formatter
	black invisible_hand

lint:
	pyflakes invisible_hand

test:
	pytest -s -v

test-cov:
	# see test coverage report
	pytest --cov=invisible_hand tests