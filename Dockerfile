FROM python:3

# environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV app_port 8001

RUN apt-get update -y
RUN apt-get -y install apt-utils vim binutils libproj-dev redis-server python3-virtualenv

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

COPY . /arielinstaller/
WORKDIR /arielinstaller
RUN pip install -r requirements.txt

EXPOSE ${app_port}
EXPOSE 1000-9999
CMD ["python3", "manage.py", "runserver"]