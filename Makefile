.PHONY: clean format lint better test test-cov
ALL: test

clean:
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +

better: format lint

format:
	isort --force-single-line-imports invisible_hand

	# remove unused imports
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place invisible_hand --exclude=__init__.py

	# sort and gather imports
	isort invisible_hand

	# formatter
	black invisible_hand

format-test-src:
	isort --force-single-line-imports tests

	# remove unused imports
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place tests --exclude=__init__.py

	# sort and gather imports
	isort tests

	# formatter
	black tests

lint:
	pyflakes invisible_hand
	pyflakes tests

test:
	pytest tests -s -v

test-cov:
	# see test coverage report
	pytest --cov=invisible_hand tests