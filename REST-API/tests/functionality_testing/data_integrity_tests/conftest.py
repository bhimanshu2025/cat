import pytest
from cat import create_app, db, db2
from cat.api_utils import create_system_users, check_scheduled_jobs, schedule_sf_jobs

@pytest.fixture()
def app():
    # create a sqllite db in mem only for the duration on tests
    app = create_app()
    # use in memory database
    app.config['SQLALCHEMY_DATABASE_URI'] =  "sqlite://"
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        db2.create_all()        
        create_system_users()
        check_scheduled_jobs()
        schedule_sf_jobs()
    yield app 

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def mocker_salesforce_case_details_function(mocker):
    return mocker.patch('cat.utils.cases.utils.salesforce_case_details')

@pytest.fixture
def mock_sf_case_object():
   class sf_case(object):
        case_owner = "test_user"
        account_name = "XYZ"
        subject = "Test_Subject"
        created_date = ""
        case_id = "2023-0910-029384"
        status = ""
        product_series = "P1"
        platform = ""
        priority = "P2"
        last_external_update_email = ""
        last_external_update_utc_time = ""
        last_external_update_note = ""
   return sf_case()