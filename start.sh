#!/usr/bin/bash

set -u
set -e

echo "Start application using Uvicorn🔥"
exec uvicorn main:app --host $APP_HOSTNAME --port $APP_PORT
