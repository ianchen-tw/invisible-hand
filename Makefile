.PHONY: clean
ALL:
clean:
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} + 