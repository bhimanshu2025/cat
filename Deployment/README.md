OPTION 1 (RECOMMENDED FOR PRODUCTION): Kubernetes
Follow cat/Deployment/kubernetes/README.md to deploy the two tier app (mysql db and the cat app)



OPTION 2 (RECOMMENDED FOR DEV AND TESTING): Docker
Follow cat/Deployment/Docker/README.md to deploy the two tier app (mysql db and the cat app)



OPTION 3 (RECOMMENDED FOR DEV ONLY): Raw install 

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
git config --global user.name "Himanshu Bahukhandi"
git config --global user.email "himanshu.surendra@gmail.com"

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


Run flask
cd /root/cat/REST-API/
python run.py

OR
cd /root/cat/REST-API/
export FLASK_APP=run.py
export FLASK_DEBUG=1
flask run --host 0.0.0.0  <Access over host or vm ip and port 5000>
or 
flask run <access over localhost and port 5000>


(Make sure sqlite3 package is installed if using local db)
create local sqlite DB (OPTIONAL, one time only - may need to edit the run.py and cat/__init__.py for below to work)

[root@vm23 ~]# cd experiments/flask_cat/
[root@vm23 flask_cat]# ls
cat.py  forms.py  __pycache__  README.md  static  templates
[root@vm23 flask_cat]# python3
Python 3.6.8 (default, Jun 20 2023, 11:53:23) 
[GCC 4.8.5 20150623 (Red Hat 4.8.5-44)] on linux
Type "help", "copyright", "credits" or "license" for more information.
from cat import db
/usr/local/lib/python3.6/site-packages/flask_sqlalchemy/__init__.py:873: FSADeprecationWarning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in the future.  Set it to True or False to suppress this warning.
  'SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and '
from cat import db
db.drop_all()
db.create_all()

db.session.commit()


Flask Alembic
make sure the init functions called in __init__.py for app are commented like create jobs etc
flask db migrate -m "added sf_mist_product column to product"   << Creates a version locally>>
flask db upgrade   <<Pushes the version changes to DB>>
