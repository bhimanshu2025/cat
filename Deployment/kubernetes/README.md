>[!NOTE]
>We expect you to have a kubernetes environment ready before following below steps

# STEP 1: 
Download the repo on node where you deploy resources in your k8 environment
```
cd /root/
git clone https://github.com/bhimanshu2025/cat.git
```

# STEP 2: 
Copy or mount the schema.sql file from /root/cat/REST-API/cat/mysql/schema.sql to /mnt/sql_tmp/ directory on node where mysql pod will be running.
I had 3 worker nodes. I created  /mnt/sql_tmp/  directory on all 3 nodes and copied the schema.sql file into it

# STEP 3: 
Deploy mysql app (this will also create mysql db "cat" and load schema from /root/cat/REST-API/cat/mysql/scehma.sql file). Edit the file to change 
the cat app version if needed. I am passing only one env variable to the cat app container which is the SQLALCHEMY_DATABASE_URI but there are other variables that can passed to the app as env variables. Refer cat/REST-API/cat/config.py for list all variables. In addition to these variables, there is also a special variable that cat app container accepts "WORKERS" when passsed as env variable. It initializes gunicorn with number of workers defined with this variable. Default is 1.
```
cd /root/cat/Deployment/kubernetes/manifests/mysql
kubectl apply -f mysql-depl.yml
```

>[!NOTE]
> The deployment will create a single mysql instance with mysql db directory mapped to /mnt/mysql. Ideally this directory should be a common mount on all worker nodes.

# STEP 4: 
Deploy cat app (Edit the docker image tag if needing a different app version)
```
cd /root/cat/Deployment/kubernetes/manifests/cat_app
kubectl apply -f cat-depl.yml
```

# STEP 4: 
Make sure the 2 pods are running
```
\# kubectl get pods -o wide
NAME                                READY   STATUS    RESTARTS   AGE     IP           NODE      NOMINATED NODE   READINESS GATES
catapp-deployment-c6996858b-4zmnp   1/1     Running   0          39s     10.244.2.2   worker2   <none>           <none>
mysql-7dd8b8c9c5-b4rbx              1/1     Running   0          2m37s   10.244.3.3   worker3   <none>           <none>
```

# STEP 5: 
Access the UI at http://<node ip>:30080/login where node ip is the IP address of worker2 node

>[!NOTE]
> The mysql password set in the same manifest file is "Catty123"



# References: 
Multinode HA k8 deployment https://www.linuxtechi.com/setup-highly-available-kubernetes-cluster-kubeadm/
