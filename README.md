# GitHub Python Projects Runner

## Installation

### Install all dependencies
```bash
sudo apt update
sudo apt install redis-server python3-virtualenv
sudo systemctl restart redis.service
virtualenv -p python3 .env
pip install -r requirements.txt
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
```

##### Prod
```bash
gunicorn -b 0.0.0.0:8001 config.wsgi --daemon
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