#!/bin/bash

w="${WORKERS:=1}"

echo "worker value is $WORKERS"

cd /var/www/cat/REST-API/
service nginx start
gunicorn --workers $w run:app
