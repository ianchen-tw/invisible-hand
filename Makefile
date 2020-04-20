.PHONY: clean
ALL: test

clean:
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +

test:
	pytest -s -v

test-cov:
	# see test coverage report
	pytest --cov=invisible_hand tests