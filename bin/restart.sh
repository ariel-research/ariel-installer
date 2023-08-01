#!/bin/bash

cd $HOME/arielinstaller/ && source .env/bin/activate
gunicorn -b 0.0.0.0:8001 config.wsgi --daemon
nohup python manage.py rqworker default low &
nohup python manage.py rqscheduler &