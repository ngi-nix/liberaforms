#!/bin/sh

set -e

sudo docker build ../../ -t liberaforms-dev:latest
sudo docker-compose up -d
