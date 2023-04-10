#!/usr/bin/env sh

set -xe

python -m venv .venv
source .venv/bin/activate
pip install poetry

poetry install