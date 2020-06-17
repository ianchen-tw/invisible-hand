#! /usr/bin/env bash

curl https://pyenv.run | bash

pyenv update && pyenv install 3.7.7
pyenv local 3.7.7
pip install pipenv
pipenv install  && pipenv install -e .