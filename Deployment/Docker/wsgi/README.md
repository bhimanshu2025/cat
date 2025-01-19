On a node with docker installed, follow below steps. Edit the cat/Deployment/Docker/wsgi/Dockerfile to modify the version/tag

git clone https://css-git.juniper.net/bhimanshu/cat.git
cd /root/cat/Deployment/Docker/wsgi/
docker build -t bhimanshu/cat:beta .

for pushing to internal repo
docker tag bhimanshu/cat:beta1 10.85.216.114:5000/bhimanshu/cat:beta
docker push 10.85.216.114:5000/bhimanshu/cat:beta

For pushing to upstream docker repo
docker push bhimanshu/cat:beta

For running the container
docker run -d -p 8080:80 bhimanshu/cat:beta

Note1: I faced issues with the wsgi module when deploying in k8 or in containers. If i didnt set the correct IP in /etc/apache2/sites-available/flaskapp.conf, the
wsgi app wont load python app. Correct IP in this case is the nodes IP where container is running. Need to work on this later. For now i plan to use gunicorn.

Note2: If WORKERS is more than 1 or there are more than one cat app pod in a k8 environment, you will notice incosistent results with jobs relating to scheduling tasks like scheduling user status change requests or fetching salesforce cases jobs. This is because each instance of app has a scheduler running and the flasks APscheduler doesnt offer HA capabilities. I will work on this in future if time/interest permits. 