#!/bin/bash
cd /home/ubuntu/A2/ece1779A2/UserUI
source venv/bin/activate
./venv/bin/gunicorn --bind 0.0.0.0:420 --workers=8 --worker-class gevent --access-logfile access.log --error-logfile error.log --timeout=60 app:webapp
