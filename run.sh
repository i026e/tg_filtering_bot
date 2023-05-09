#!/usr/bin/env bash

set -xe

source .venv/bin/activate

alembic upgrade head
poetry run filtering_bot
