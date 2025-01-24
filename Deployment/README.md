

# OPTION 1: Raw install 

## STEP 1
Install Ubuntu 18.04.4 VM or a machine with Ubuntu 18.04.4 (All the testing has been done on this version as of today)

## STEP 2
Install python3, git and other packages  
```
apt-get update
apt-get -y install python3
apt-get -y install python3-pip
apt-get -y install python3-venv
apt-get -y install git
```

## STEP 3
Download application from git repo 
```
cd /root/
git clone https://github.com/bhimanshu2025/cat.git
cd cat
git config --global user.name "FirstName LastName"
git config --global user.email "abcd@gmail.com"
```

## STEP 4
Create python3 evnv
```
cd /root/
python3 -m venv venv
source venv/bin/activate
```
OR (If using Visual Studio Code)
```
In visual studio select "Python: Create Environment" in command Pallete ctrl+shift+p (had to install python extension first)
```

## STEP 5
Install Flask and other dependencies <These packages get installed when creating venv if using python extension in visual studio>
```
cd /root/cat/
pip install --upgrade pip
pip install -r requirements.txt
```

## STEP 6
Start the Application
```
cd /root/cat/REST-API/
export FLASK_APP=run.py
export FLASK_DEBUG=1  <Optional if you want to run in debug mode>
flask run --host 0.0.0.0  <Access over host or vm ip and port 5000>
or 
flask run <access over localhost and port 5000>
```
OR (to run on localhost only https://localhost:5000)
```
cd /root/cat/REST-API/
python run.py
```

## STEP 7
Access the Application through a browser at http://<server IP>:5000

# OPTION 2: Kubernetes
Follow cat/Deployment/kubernetes/README.md to deploy the two tier app (mysql db and the cat app)

# OPTION 3: Docker
Follow cat/Deployment/Docker/README.md to deploy the two tier app (mysql db and the cat app)

