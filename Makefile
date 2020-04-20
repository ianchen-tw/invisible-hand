.PHONY: clean
ALL: test

clean:
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +
test:
	pytest -s -v