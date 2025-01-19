import os, json

class Config:
    ENVIRONMENT = os.environ.get('ENVIRONMENT') or "DEV"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ee9d062f9ee600575c1876cd2854bfbc'
    VERSION = "v1.12"
    BUILD = "v1.12"
    PRIORITY_LIST = os.environ.get('PRIORITY_LIST') or ['P1', 'P2', 'P3', 'P4']
    # SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///cat.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'sqlite:///cat.db'
    if os.environ.get('SQLALCHEMY_BINDS'):
        SQLALCHEMY_BINDS = json.loads(os.environ.get('SQLALCHEMY_BINDS')) 
    else: 
        SQLALCHEMY_BINDS = {'provision': 'sqlite:///provision.db'}
    EXTERNAL_CASE_UPDATE_CHECK_INTERVAL = os.environ.get('EXTERNAL_CASE_UPDATE_CHECK_INTERVAL') or 60  # in minutes, defaults to hourly
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or "admin"
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or "smtp.gmail.com"
    MAIL_PORT = os.environ.get('MAIL_PORT') or 25
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or False
    MAIL_NO_REPLY_SENDER = os.environ.get('MAIL_NO_REPLY_SENDER') or "cat-do-not-reply@gmail.com"
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or "catadmin@gmail.com"
    # Bearer token is obsolete and no longer used in the app.
    BEARER_TOKEN = os.environ.get('BEARER_TOKEN') or \
        "00DDC00000041rF!ARQAQO5DWjCB7rVAW62vnbba8n6OMrrh4mSov6Wn3Lj_.z0dAxm1Sta85M.4MAA7XSA9.bl1OqBKuvStbAY53RUnWmjYj6Vw"
    SF_CLIENT_ID = os.environ.get('SF_CLIENT_ID')
    SF_CLIENT_SECRET = os.environ.get('SF_CLIENT_SECRET')
    SF_TOKEN_URL = os.environ.get('SF_TOKEN_URL')
    SF_INSTANCE_URL = os.environ.get('SF_INSTANCE_URL') or None
    SF_USERNAME = os.environ.get('SF_USERNAME')
    SF_PASSWORD = os.environ.get('SF_PASSWORD')
    SF_GRANT_TYPE = os.environ.get('SF_GRANT_TYPE')
    SF_EXTERNAL_EMAIL = os.environ.get('SF_EXTERNAL_EMAIL') or None
    # comma separated emails to send sf api req summary report
    if os.environ.get('SF_API_REQ_REPORT_EMAILS_LIST'):
        SF_API_REQ_REPORT_EMAILS_LIST = os.environ.get('SF_API_REQ_REPORT_EMAILS_LIST').split(',') 
    else:
        SF_API_REQ_REPORT_EMAILS_LIST = ""
    SF_API_REQ_REPORT_INTERVAL = os.environ.get('SF_API_REQ_REPORT_INTERVAL') or 7 # In days 
