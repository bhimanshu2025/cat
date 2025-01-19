We are using pytest framework for testing here.
Each test case creates a temp db instance in memory which gets teared down at the end of the test

So far the test cases are devided into API(api endpoints and backend functional testing) and routes (mosttly UI)

I havent done much testing on rbac. eg a user from a different team shoudnt be able to edit other teams user etc. - TODO

"case_assignment_test_cases" is a scenario based test case that was manually verified. It verifies the case distribution algorithm.

Notes: Debugging test failures or tests not resulting in the way we intend to
OPTION1 pytest test_users.py::test_37_reactivate_user_post_2_400  -rP  < enable print statements inside test functions to print the data from html pages>
OPTION2 enable pdb in code and run above pytest command 

Note: As i found out today, when test cases are run together, there is data that persists between test cases. For example if test_1 creates a job, the when test 1 and test 2 are executed together, test 2 "state" will an existing job created in test 1. If test 2 is run  individually, then there is no persistent data. Need more research into this as i was under impression each test case destroys the in memory sqllite db and creates new one.

Sequence of testing:
1. First test the tests/functionality_testing/api/ test cases in following order ideally
test_teams_api.py
test_products_api.py
test_users_api.py
test_userproduct_api.py
test_cases_api.py
test_audit_api.py

2. then test the tests/functionality_testing/routes in the following order ideally
test_teams.py
test_products.py
test_users.py
test_main.py

3. then test the tests/functionality_testing/data_integrity_tests in following order ideally

