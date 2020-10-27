#! /bin/sh
# This file should be runned in container

# Sort imports one per line, so autoflake can remove unused imports
isort --force-single-line-imports invisible_hand

# remove unused imports
autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place invisible_hand --exclude=__init__.py

# sort and gather imports
isort invisible_hand

# formatter
black invisible_hand
