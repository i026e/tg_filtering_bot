#!/usr/bin/env sh

set -xe

WORKING_DIR="$(pwd)"
USER="$(whoami)"

sed -e "s|REPLACE_WORKING_DIR|${WORKING_DIR}|g"  -e "s|REPLACE_USER|${USER}|g" tg_filtering_bot.service.template > tg_filtering_bot.service

sudo cp tg_filtering_bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tg_filtering_bot.service
sudo systemctl start tg_filtering_bot.service
