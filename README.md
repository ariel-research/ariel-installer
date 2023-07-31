# GitHub Python Projects Runner

## Installation

### Install all dependencies
```bash
sudo apt update
sudo apt install redis-server python3-virtualenv
sudo systemctl restart redis.service
cd <project_folder>
virtualenv -p python3 .env
source .env/bin/activate
pip install -r requirements.txt --use-deprecated=legacy-resolver
python3 manage.py migrate
mkdir ../github_projects
```

### Create superuser
```bash
python manage.py createsuperuser
```

### Run application
##### In Debug mode
```bash
python manage.py runserver 0.0.0.0:8001
python manage.py flushqueue --queue default
python manage.py flushqueue --queue low
```

Next two commands in different shell tabs:
```bash
python manage.py rqscheduler
python manage.py rqworker default low 
```

##### Prod
```bash
gunicorn -b 0.0.0.0:8001 config.wsgi --daemon
python manage.py flushqueue --queue default
python manage.py flushqueue --queue low
nohup python manage.py rqscheduler &
nohup python manage.py rqworker default low &
```

Install crontab on Prod to start the project after reboot automatically

```bash
@reboot     cd /home/david/arielinstaller/ && source .env/bin/activate && gunicorn -b 0.0.0.0:8001 config.wsgi --daemon
@reboot     cd /home/david/arielinstaller/ && source .env/bin/activate && nohup python manage.py rqworker default low &
@reboot     cd /home/david/arielinstaller/ && source .env/bin/activate && nohup python manage.py rqscheduler &
```

or in Docker

```bash
docker-compose up --build
docker-compose -f docker-compose.yml up --remove-orphans
```

### Prune the images
```bash
docker image prune -f
docker container prune -f
```

Now you can access the project admin panel using the superuser created above by following URL:
```bash
http://127.0.0.1:8001/admin
```