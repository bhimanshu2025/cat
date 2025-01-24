

OPTION 1: Raw install 

Install Ubuntu 18.04.4 VM

Install python3 and git
apt-get update
apt-get -y install python3
apt-get -y install python3-pip
apt-get -y install python3-venv
apt-get -y install git

download the git repo 
cd /root/
git clone https://github.com/bhimanshu2025/cat.git
cd cat
git config --global user.name "FirstName LastName"
git config --global user.email "abcd@gmail.com"

create python3 evnv
In visual studio select "Python: Create Environment" in command Pallete ctrl+shift+p (had to install python extension first)
OR
cd /root/
python3 -m venv venv
source venv/bin/activate

Install Flask and other dependencies <These packages get installed when creating venv if using python extension in visual studio>
cd /root/cat/
pip install --upgrade pip
pip install -r requirements.txt

cd /root/cat/REST-API/
export FLASK_APP=run.py
export FLASK_DEBUG=1  <Optional if you want to run in debug mode>
flask run --host 0.0.0.0  <Access over host or vm ip and port 5000>
or 
flask run <access over localhost and port 5000>

OR (to run on localhost only https://localhost:5000)

Run flask
cd /root/cat/REST-API/
python run.py


(Make sure sqlite3 package is installed if using local db)
# dpkg -l | grep sql
ii  libsqlite3-0:amd64               3.22.0-1ubuntu0.3                           amd64        SQLite 3 shared library

create local sqlite DB (OPTIONAL, one time only - may need to edit the run.py and cat/__init__.py for below to work)

[root@vm23 ~]# cd /root/cat/REST-API
(venv) root@vm8:~/cat/REST-API# ls
cat  migrations  run.py  tests
(venv) root@vm8:~/cat/REST-API# python
Python 3.6.9 (default, Mar 10 2023, 16:46:00) 
[GCC 8.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from cat import db
/usr/local/lib/python3.6/site-packages/flask_sqlalchemy/__init__.py:873: FSADeprecationWarning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in the future.  Set it to True or False to suppress this warning.
  'SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and '

>>> db.drop_all()

>>> db.create_all()

>>> db.session.commit()


OPTION 2: Kubernetes
Follow cat/Deployment/kubernetes/README.md to deploy the two tier app (mysql db and the cat app)


OPTION 3: Docker
Follow cat/Deployment/Docker/README.md to deploy the two tier app (mysql db and the cat app)

