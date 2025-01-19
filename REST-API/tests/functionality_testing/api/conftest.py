import pytest
from cat import create_app, db, db2
from cat.api_utils import create_system_users, check_scheduled_jobs, schedule_sf_jobs

@pytest.fixture()
def app():
    # create a sqllite db in mem only for the duration of tests
    app = create_app()
    # use in memory database
    app.config['SQLALCHEMY_DATABASE_URI'] =  "sqlite://"
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