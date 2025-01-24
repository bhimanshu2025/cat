## CAT
The tool is intended for teams that want to distribute cases/tickets among their team members

# SUMMARY
At its core the tool distributes cases between members of a team or teams supporting a product. Each product can have its own load distribution settings. The tool also ingrates with external tools like salesforce and microsoft teams. 

# FEATURES
1. Admin user is a predefined user and its password is configured through the config file. 
2. Admin user can create other admin users, teams and products. The admin user can also associate users with products
3. Once a user is associated with a product, they are part of round robin case distribution cycle
4. User status can be disabled for all products or specific ones to not get any cases
5. The tool also allows scheduling of tasks such as user status change, user shift timing change.
6. There are options to integrate the tool with Microsoft teams using teams incoming webhooks.
7. There are options to integrate the tool with SalesForce to fetch list of newly created cases periodically and automatically CAT them.
8. The tool also offers options to configure initial response email that can be posted on a case on behalf of user during CAT auto-cases assignment.
9. Most of the UI operations can be performed using REST API that the tool exposes.
10. Tracks all operations under Audit history.

>[!Note]
>For deployment instructions refer cat/Deployments/README.md

# Case Assignment Logic (Internal functioning of Application)

The initial goal is to find List of eligible users to assign the case to. Inorder to understand the logic behind finding the list of eligible users, its important to understand below variables


| Variable name | Applies to Entity | Default value | Description |
|---------------|-------------------|---------------|-------------|
| max_days | Product | (2) |starting today, looks back "max_days" until it finds "one" user with least cases. Example: Suppose max_days=2 and there are 3 users that the case can be assigned to. The logic will first check how many cases each user got today. It will create a list of users that got least number of cases.  If the result is more than one user, it looks at number of cases assigned between today and today-1 and then between today and today-2 and so on. The logic will keep looking back(increments of one day) until it finds one user or it reaches "max_days" which in this case will be today and today-2. If it cant find one user, it moves on to looking backwards monthly basis(explained below). |
| max_days_month | Product | (300) |starting today, looks back "max_days_month" until it finds "one" user with least cases. Example: Suppose max_days_month=300 and there are 3 users. The logic will first check how many cases each user got today. It will create a list of users that got least number of cases.  If the result is more than one user, it looks at number of cases assigned between today and today-30 and then between today and today-60 and so on.  The logic will keep looking back(increments of 30 days) until it finds one user or it reaches "max_days_month" which in this case will be today and today-300. If it cant find one user, the final tie-breaker is username. |
| quota | UserProduct | (1) | Defines how many cases other users in the formulated list should get assigned over "quota_days" before this user gets their first case. For Example: Suppose the formulated list of users that a case can be assigned has 3 users u1 with quota 1, u2 with quota 2, u3 with quota 1, u4 with quota 3. The "quota_days" variable is set to 2. User u2 will recieve a case only after u1 and u3 have got 2 cases each in past 2 days. u4 will recieve a case only after u1, u2 and u3 each have got 3 cases in past 2 days. Quota value can't be 0. |
| quota_days | Product | (1) | This variable is used to decide how many days to look back for a users case count and then the value is used for comparision againt quota. |
| strategy | Product | (s1) |This variable is used to decide the case count for users when computing the eligible list of users to assign a case to. s1 strategy counts users cases taken across all products whereas s2 strategy counts cases taken for the product this strategy is applied. For example: Consider a user u1 who has taken 2 cases belonging to products P1 and P2. User u1 also supports product P3 which has strategy set to s2. In that case when the eligible list of users is compiled to assign next case to, u1's case count will be 0. Similarly all other users supporting P3 will have their case count computed. |

Below is the logic to find the eligible list of users to assign a case 'x' that belongs to product 'P1'

Find initial list of users that the case can be assigned to by following below rules
1. Find all users that support the product
2. Filter out users that are not in shift
3. Filter out users that are inactive for this product or are set to inactive status

Once the list of eligible users is compiled, keep running the below loop until list contains one user that the case can be assigned to
1. case count of all eligible users for today. If the min case count has more than one user go to step 2 for only the users with min case count
2. case count of all eligible users for today and today -1.  If the min case count has more than one user go to step 3 for only the users with min case count
3. keep repeating above one to find case count until we find single user or reach "max_days" limit. So if "max_days" is 3, keep looking back until today - 3 days
4. If "max_days" cant decide who to assign a case to (has more than one user in list), get case out of only those users with min cases from above "min_days" list for last 30 days. 
5. if step 4 also results into more than one eligible user, get case count of users with min cases from previous step over past 30+30 days
6. keep repeating 5 until we find single user or reach the "max_days_month" limit. So if max_days_month is set to 300, lookup will happen max 10 times recursively if it doesnt find a single user. 
7. final tie breaker is user name. So if two users "apple" and "banana" are tied after step 6, the tie break will result in favor of apple.


# UI/API Enforced Rules:
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








