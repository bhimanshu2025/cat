from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint
import logging
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_apscheduler import APScheduler
from flask_mail import Mail
from cat.config import Config
from cat.cache import cache

db = SQLAlchemy()
db2 = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
scheduler = APScheduler()
scheduler_sf = APScheduler()
login_manager = LoginManager()
login_manager.login_view = 'users_b.login'
login_manager.login_message_category = 'info'
migrate=Migrate() #Initializing migrate.

def create_app(config_class=Config):
    app = Flask(__name__)
    with app.app_context():
        app.config.from_object(Config)

        root = logging.getLogger()
        app.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s:[%(levelname)s]:[%(name)s] : [%(threadName)s] : %(message)s")
        file_handler = logging.FileHandler('/tmp/cat.log')
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
        # stream_handler = logging.StreamHandler()
        # stream_handler.setFormatter(formatter)
        # root.addHandler(stream_handler)

        SWAGGER_URL = '/swagger'  # URL for exposing Swagger UI (without trailing '/')
        API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)
        # Call factory function to create our blueprint
        swaggerui_blueprint = get_swaggerui_blueprint(
            SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
            API_URL,
            config={  # Swagger UI config overrides
                'app_name': "CAT"
            },
            # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
            #    'clientId': "your-client-id",
            #    'clientSecret': "your-client-secret-if-required",
            #    'realm': "your-realms",
            #    'appName': "your-app-name",
            #    'scopeSeparator': " ",
            #    'additionalQueryStringParams': {'test': "hello"}
            # }
        )
        app.register_blueprint(swaggerui_blueprint)

        if scheduler.state == 0:
            scheduler.init_app(app)
            scheduler.start()
        if scheduler_sf.state == 0:
            scheduler_sf.init_app(app)
            scheduler_sf.start()
        mail.init_app(app)
        db.init_app(app)
        db2.init_app(app)
        db.create_all()
        db2.create_all()
        bcrypt.init_app(app)
        login_manager.init_app(app)

        # Bootstrap
        app.logger.info(f"Connected to database {db.engine.url}")
        from cat.api_utils import create_system_users, check_scheduled_jobs, schedule_sf_jobs, audit_sf_api_requests
        create_system_users()
        check_scheduled_jobs()
        schedule_sf_jobs()
        app.case_cache = cache.CatCache('case_cache')
        app.sf_token = 'sd'
        if app.config['SF_API_REQ_REPORT_EMAILS_LIST'] and app.config['SF_API_REQ_REPORT_INTERVAL'] \
            and scheduler_sf.get_job(id='audit_sf_api_requests') is None:
            scheduler_sf.add_job(id=f"audit_sf_api_requests", func=audit_sf_api_requests, 
                                    trigger='interval', days=app.config['SF_API_REQ_REPORT_INTERVAL'])

        from cat.main.routes import main
        from cat.users.routes import users_b
        from cat.teams.routes import teams_b
        from cat.products.routes import products_b
        from cat.api.cases.routes import cases
        from cat.api.users.routes import users
        from cat.api.teams.routes import teams
        from cat.api.audit.routes import auditing
        from cat.api.products.routes import products
        from cat.api.userproduct.routes import ups
        from cat.errors.handlers import errors

        app.register_blueprint(main)
        app.register_blueprint(users_b)
        app.register_blueprint(teams_b)
        app.register_blueprint(products_b)
        app.register_blueprint(cases)
        app.register_blueprint(users)
        app.register_blueprint(teams)
        app.register_blueprint(auditing)
        app.register_blueprint(products)
        app.register_blueprint(ups)
        app.register_blueprint(errors)
        
        migrate.init_app(app, db, render_as_batch=True)

        return app 