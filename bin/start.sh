#!/bin/bash

python manage.py migrate
python manage.py flushqueue --queue default
python manage.py flushqueue --queue low
python manage.py rqworker -v 3 default &
python manage.py rqworker -v 3 low &
python manage.py runserver 8000 &
