DEV PURPOSE ONLY (FOR DEPLOYMENT REFER - https://css-git.juniper.net/bhimanshu/cat/-/blob/master/kubernetes/README.md)
Deploy cat app:

kubectl apply -f cat-deploy.yml 

Needs a mysql db service deployed by name "mysql" in same namespace


Todo: the SQLALCHEMY_DATABASE_URI env variable can be broken down into mysql db, db password, db user, host ip etc saved in a configmap and passed to the cat app container as env variables which the cat app container config.py can process and compute the SQLALCHEMY_DATABASE_URI string.