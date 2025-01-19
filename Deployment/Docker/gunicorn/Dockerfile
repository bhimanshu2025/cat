FROM ubuntu:18.04
MAINTAINER bhimanshu@juniper.net
RUN apt-get update
RUN apt-get -y install nginx git \
    python3-pip python3-venv
RUN rm -f /etc/nginx/sites-enabled/default
COPY cat /etc/nginx/sites-enabled/
COPY entrypoint.sh /root
WORKDIR /var/www/
RUN git clone https://css-git.juniper.net/bhimanshu/cat.git -b beta1
RUN pip3 install --upgrade pip && pip3 install -r /var/www/cat/requirements.txt
WORKDIR /root/
ENTRYPOINT ./entrypoint.sh
EXPOSE 443 80
