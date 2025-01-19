DEV PURPOSE ONLY (FOR DEPLOYMENT OF APP REFER - https://css-git.juniper.net/bhimanshu/cat/-/blob/master/kubernetes/README.md)
Deploy mysql app and service (creates persistent volumes, pvc and secrets)

kubectl apply -f mysql-depl.yml 

Database restore: Below command is to load db schema into database named "cat"

kubectl exec mysql-54956869f9-4rkt6 --  sh -c 'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" cat' < /root/cat/REST-API/cat/mysql/schema.sql

Database backup:

backup database "cat" 
kubectl exec mysql-54956869f9-4rkt6 --  sh -c 'exec mysqldump --no-data cat -uroot -p"$MYSQL_ROOT_PASSWORD"' > /root/cat/REST-API/cat/mysql/schema.sql

All database
kubectl exec mysql-54956869f9-4rkt6 --  sh -c 'exec mysqldump --no-data --all-databases -uroot -p"$MYSQL_ROOT_PASSWORD"' > /root/cat/REST-API/cat/mysql/schema.sql
