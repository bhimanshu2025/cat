SUMMARY: At its core the tool distributes cases between members of a team or teams supporting a product. Each product can have its own load distribution settings. The tool also ingrates with external tools like salesforce and microsoft teams. The goal is to be able to adapt to existing tools so from the end users perpective they can keep using the existing tools for most of their daily tasks. The tool should be able to do its job talking to infrastructure that already exists. Another goal is to do provide a platform for teams to build modules for doing some initial case analysis when a case is assigned. The teams supporting products have the expert knowledge that to an extent can be utilized in doing initial analysis. The tool will provide the ability to onboard such modules that the tool can then use to apply on data fetched from salesforce

For deployment instructions refer cat/Deployments/README.md

To take a db schema backup of sqlite db
sqlite3 cat.db '.schema' > sql_lite/schema.sql

To connect to remote db 
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Cat123@10.85.60.7:32001/cat"
<< install pymysql lib using pip>>

To test reading DB objects
root@vm23 flask_cat]# python3
Python 3.6.8 (default, Jun 20 2023, 11:53:23) 
[GCC 4.8.5 20150623 (Red Hat 4.8.5-44)] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from cat import db
/usr/local/lib/python3.6/site-packages/flask_sqlalchemy/__init__.py:873: FSADeprecationWarning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in the future.  Set it to True or False to suppress this warning.
  'SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and '
>>> from cat import User, Team, Product, UserProduct
>>> User.query.all()
[User'colson', 'T2', '2023-09-13 19:55:43.765565', User'vinay', 'T3', '2023-09-13 19:55:43.765584']
>>> User.query.first()
User'colson', 'T2', '2023-09-13 19:55:43.765565'




Flask Database versioning
https://flask-migrate.readthedocs.io

pip3 install Flask-Migrate

export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration."
flask db upgrade



TO DO
1. Understand db schema upgrade and downgrade using alembic

3. implement unit test cases 

5. if in HA how to manage scheduled jobs
6. track user active status
7. integrate with salesforce
8. integrate with mule

10. datetime format in audit

DB Schema:
User

Product

Team

UserProduct

Cases

Audit

Jobs

SalesforceCases

Case Assignment Logic :-

STEP 1: The initial goal is to find List of eligible users to assign the case to. Inorder to understand the logic behind finding the list of eligible users, its important to understand below variables


Variable name      Applies to Entity       Default value      Description
max_days           Product                 (2)                starting today, looks back "max_days" until it finds "one" user with least cases. Example: Suppose max_days=2 and there are 3 users that the case can be assigned to. The logic will first check how many cases each user got today. It will create a list of users that got least number of cases.  If the result is more than one user, it looks at number of cases assigned between today and today-1 and then between today and today-2 and so on. The logic will keep looking back(increments of one day) until it finds one user or it reaches "max_days" which in this case will be today and today-2. If it cant find one user, it moves on to looking backwards monthly basis(explained below).

Variable name      Applies to Entity       Default value      Description
max_days_month     Product                 (300)              starting today, looks back "max_days_month" until it finds "one" user with least cases. Example: Suppose max_days_month=300 and there are 3 users. The logic will first check how many cases each user got today. It will create a list of users that got least number of cases.  If the result is more than one user, it looks at number of cases assigned between today and today-30 and then between today and today-60 and so on.  The logic will keep looking back(increments of 30 days) until it finds one user or it reaches "max_days_month" which in this case will be today and today-300. If it cant find one user, the final tie-breaker is username.

Variable name      Applies to Entity       Default value      Description
quota              UserProduct             (1)                Defines how many cases other users in the formulated list should get assigned over "quota_days" before this user gets their first case. For Example: Suppose the formulated list of users that a case can be assigned has 3 users u1 with quota 1, u2 with quota 2, u3 with quota 1, u4 with quota 3. The "quota_days" variable is set to 2. User u2 will recieve a case only after u1 and u3 have got 2 cases each in past 2 days. u4 will recieve a case only after u1, u2 and u3 each have got 3 cases in past 2 days. Quota value can't be 0.

Variable name      Applies to Entity       Default value      Description
quota_days         Product                 (1)                This variable is used to decide how many days to look back for a users case count and then the value is used for comparision againt quota.

Variable name      Applies to Entity       Default value      Description
strategy           Product                 (s1)               This variable is used to decide the case count for users when computing the eligible list of users to assign a case to. s1 strategy counts users cases taken across all products whereas s2 strategy counts cases taken for the product this strategy is applied. For example: Consider a user u1 who has taken 2 cases belonging to products P1 and P2. User u1 also supports product P3 which has strategy set to s2. In that case when the eligible list of users is compiled to assign next case to, u1's case count will be 0. Similarly all other users supporting P3 will have their case count computed.

Below is the logic to find the eligible list of users to assign a case 'x' that belongs to product 'P1'

Find initial list of users that the case can be assigned to following below rules
  1.Find all users that support the product
  2.filter out users that are not in shift
  3.filter out users that are inactive for this product or are set to inactive status

In the list of eligible users, keep running the below loop until list contains one user that the case can be assigned to
1 case count of all eligible users for today. If the min case count has more than one user go to step 2 for only the users with min case count
2. case count of all eligible users for today and today -1.  If the min case count has more than one user go to step 3 for only the users with min case count
3. keep repeating above one to find case count until we find single user or reach "max_days" limit. So if "max_days" is 3, keep looking back until today - 3 days
4. If "max_days" cant decide who to assign a case to (has more than one user in list), get case out of only those users with min cases from above "min_days" list for last 30 days. 
5. if step 4 also results into more than one eligible user, get case count of users with min cases from previous step over past 30+30 days
6. keep repeating 5 until we find single user or reach the "max_days_month" limit. So if max_days_month is set to 300, lookup will happen max 10 times recursively if it doesnt find a single user. 
7. final tie breaker is user name. So if two users "apple" and "banana" are tied after step 6, the tie break will result in favor of apple.


UI/API Enforced Rules:
1. "admin: user and "global" team are created by default. If these get deleted by user or some other means, the app will recreate them when its restarted
2. "admin" user belongs to "global" team and has admin rights. Its the user that will be used to create all other entities like teams, users, products etc.
3. Only a user with admin role can create another user with admin role. 
4. The object hierarchy is as follows : 
Team => users 
So the first step is to create a team and then users can be created to be part of that team. A user can be part of only one team
5. Once team and users are created, products can be created and users can be associated with products which is many to many relationship
6. A user with admin role can view all users, all teams, all products but edit or delete only objects that are part of the team admin belongs to. For example: User u1 with admin role can view all users, products , teams but can only edit/delete users that are part of same team, products that users supports, team that the user is part of, user - product associations for all the users that are part of the team u1 belongs to.
7. Conditions in #6 does not apply to system user "admin"
8. A user with non-admin role, can view/edit/delete their own profile, their own user-product associations but view all the others data








