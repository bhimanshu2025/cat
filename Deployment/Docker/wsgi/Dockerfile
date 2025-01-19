FROM ubuntu:18.04
MAINTAINER himanshu.surendra@gmail.com
RUN apt-get update
RUN apt-get -y install apache2 libapache2-mod-wsgi-py3 git \
    python3.6-venv python3-venv
WORKDIR /var/www/flaskapp/
COPY flaskapp.wsgi /var/www/flaskapp/
COPY flaskapp.conf /etc/apache2/sites-available/
WORKDIR /root
RUN a2ensite flaskapp
RUN git clone https://github.com/bhimanshu2025/cat.git -b beta
RUN cp -ipr /root/cat/REST-API/* /var/www/flaskapp/
RUN python3 -m venv /var/www/flaskapp/venv
SHELL ["/bin/bash", "-c"]
RUN source /var/www/flaskapp/venv/bin/activate && pip install --upgrade pip && pip install -r /root/cat/requirements.txt 
CMD ["apachectl", "-D", "FOREGROUND"]
