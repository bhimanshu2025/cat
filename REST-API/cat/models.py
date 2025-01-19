from cat import db, login_manager, bcrypt, db2
from datetime import datetime, timedelta, date
from sqlalchemy import func
import pytz
from flask_login import UserMixin, current_user
from sqlalchemy.ext.hybrid import hybrid_property

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class UserProduct(db.Model):
    user_name = db.Column(db.ForeignKey('user.username'), primary_key=True)
    product_name = db.Column(db.ForeignKey('product.productname'), primary_key=True)
    active =  db.Column(db.Boolean, default=True)
    quota =  db.Column(db.Integer,default=1)

    def __repr__(self):
        return f"UserProduct'{self.user_name}', '{self.product_name}', '{self.active}', '{self.quota}'"

    @classmethod
    def query_user_product(cls, user, product, check_in_shift=True):
        up = UserProduct.query.filter_by(user_name=user.username, product_name=product.productname).first()
        if up is None:
            return f'user {user.username} doesnt support product {product.productname}'
        elif not user.active:
            return f'user {user.username} status is inactive'
        elif not up.active:
            return f'user {user.username} status is inactive for product {product.productname}'
        elif check_in_shift and not user.in_shift():
            return f'user {user.username} is not in shift'
        else: 
            return 0
    
    def update(self, d):
        if d.get('active') is not None:
            self.active = d.get('active')
        self.quota = d.get('quota') or self.quota
        return self.schema()
    
    def schema(self):
        return {
            "username": self.user_name,
            "productname": self.product_name,
            "active": self.active,
            "quota": self.quota
        }

class MuleUser(db2.Model):
    __tablename__ = "user"
    __bind_key__ = "provision"
    name = db.Column(db.String(30), primary_key=True)
    password = db.Column(db.String(100), nullable=False)

    @classmethod
    def validate_user_password(cls, username, password):
        muleuser = cls.query.filter_by(name=username, password=func.PASSWORD(password)).first()
        catuser = User.query.filter_by(username=username).first()
        if catuser and muleuser:
            catuser.login()
            return catuser
        else:
            return False
        
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100))
    password = db.Column(db.String(200), nullable=False)
    user_since = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    teamname = db.Column(db.ForeignKey('team.teamname'), nullable=False)
    products = db.relationship('Product', secondary=UserProduct.__table__, backref='supported_by', lazy=True)
    cases = db.relationship('Cases', backref='owner', lazy=True, foreign_keys = 'Cases.user', cascade="all, delete-orphan")
    assigned_cases = db.relationship('Cases', backref='assigner', lazy=True, foreign_keys = 'Cases.assigned_by')
    audits = db.relationship('Audit', backref='by_user', lazy=True)
    jobs = db.relationship('Jobs', backref='submitted_by', lazy=True)
    active = db.Column(db.Boolean, default=True)
    shift_start = db.Column(db.String(100), nullable=False, default='09:00:00')
    shift_end = db.Column(db.String(100), nullable=False, default='18:00:00')
    timezone = db.Column(db.String(200), nullable=False, default="US/Pacific")
    last_login = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    admin = db.Column(db.Boolean, default=False)
    team_email_notifications = db.Column(db.Boolean, default=False)
    salesforce_emails = db.relationship('SalesforceEmails', backref='created_by', lazy=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    monitor_case_updates = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"User'{self.username}', '{self.teamname}', '{self.id}'"
    
    @hybrid_property
    def full_name(self):
        if self.first_name is None or self.last_name is None:
            return self.username
        return self.first_name + ' ' + self.last_name
    
    def login(self):
        self.last_login = datetime.utcnow()
    
    @staticmethod
    def get_hash(str):
        return bcrypt.generate_password_hash(str).decode('utf-8')

    @staticmethod
    def check_hash(str_hash, str):
        return bcrypt.check_password_hash(str_hash, str)

    @classmethod
    def validate_user_password(cls, username, password):
        user = cls.query.filter_by(username=username).first()
        if user and cls.check_hash(user.password, password):
            user.login()
            return user
        else:
            return False

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @classmethod
    def user_names(cls):
        l = []
        for user in cls.query.all():
            l.append(user.username)
        return l

    def product_names(self):
        l = []
        for product in self.products:
            l.append(product.productname)
        return l

    def sf_email_names(self):
        l_email_names = []
        for email in self.salesforce_emails:
            l_email_names.append(email.email_name)
        return l_email_names
    
    def update(self, d):
        self.email = d.get('email') or self.email
        if d.get('password'):
            pwd_hash = self.get_hash(d.get('password'))
            self.password = pwd_hash
        self.teamname = d.get('teamname') or self.teamname
        if d.get('active') is not None:
            self.active = d.get('active')
        self.shift_start = d.get('shift_start') or self.shift_start
        self.shift_end = d.get('shift_end') or self.shift_end
        self.first_name = d.get('first_name') or self.first_name
        self.last_name = d.get('last_name') or self.last_name
        self.timezone = d.get('timezone') or self.timezone
        if d.get('admin') is not None:
            self.admin = d.get('admin')
        if d.get('team_email_notifications') is not None:
            self.team_email_notifications = d.get('team_email_notifications')
        if d.get('monitor_case_updates') is not None:
            self.monitor_case_updates = d.get('monitor_case_updates')
        return self.schema()
    
    @classmethod
    def add_user(cls, d):
        pwd_hash = cls.get_hash(d.get('password'))
        user = cls(username=d.get('username'), email=d.get('email'), password=pwd_hash, teamname=d.get('teamname'), 
                active=d.get('active'), shift_start=d.get('shift_start'), shift_end=d.get('shift_end'), 
                timezone=d.get('timezone'), admin=d.get('admin'), team_email_notifications=d.get('team_email_notifications'),
                first_name=d.get('first_name'), last_name=d.get('last_name'), monitor_case_updates=d.get('monitor_case_updates'))
        return user
    
    # returns a tz aware datetime object of when the user shift starts today
    def shift_start_datetime(self):
        s1 = datetime.now(pytz.timezone('US/Pacific')).strftime('%Y/%m/%d') + ' ' + self.shift_start
        return pytz.timezone(self.timezone).localize(datetime.strptime(s1 , '%Y/%m/%d %H:%M:%S'))
    
    # returns a tz aware datetime object of when the user shift ends today
    def shift_end_datetime(self):
        s2 = datetime.now(pytz.timezone('US/Pacific')).strftime('%Y/%m/%d') + ' ' + self.shift_end
        return pytz.timezone(self.timezone).localize(datetime.strptime(s2,'%Y/%m/%d %H:%M:%S'))

    # checks if user is currently in shift or not. If at_time (eg 16:00:00) is give, then checks if user is in shift at
    # 4pm or not
    def in_shift(self, at_time=None):
        s1 = datetime.now(pytz.timezone('US/Pacific')).strftime('%Y/%m/%d') + ' ' + self.shift_start
        s2 = datetime.now(pytz.timezone('US/Pacific')).strftime('%Y/%m/%d') + ' ' + self.shift_end
        if at_time:
            s3 = datetime.now(pytz.timezone('US/Pacific')).strftime('%Y/%m/%d') + ' ' + at_time
            compare_time = pytz.timezone(self.timezone).localize(datetime.strptime(s3 , '%Y/%m/%d %H:%M:%S'))
        else:
            compare_time = datetime.now(tz=pytz.UTC)
        # convert time into timezone aware time and then compare with current time. Current time is fetched in UTC
        start_time = pytz.timezone(self.timezone).localize(datetime.strptime(s1 , '%Y/%m/%d %H:%M:%S'))
        end_time = pytz.timezone(self.timezone).localize(datetime.strptime(s2,'%Y/%m/%d %H:%M:%S'))
        if start_time <= compare_time and end_time > compare_time:
            return True
        else:
            return False

    # returns number of cases assigned to user in last x days
    # if p_name is specified, filters it based on that product
    def number_of_cases(self, x=0, p_name=None):
        f_date = datetime.utcnow().date() - timedelta(days=x)
        l_date = datetime.utcnow().date()
        return len(Cases.get_all_cases_of_user(self.username, f_date, l_date)) if p_name == None else \
                len(Cases.get_all_cases_of_user(self.username, f_date, l_date, p_name))

    # returns number of cases assigned to user in last x months
    def monthly_cases(self, x=0):
        pass

    # returns number of cases assigned to user in last x years
    def yearly_cases(self, x=0):
        pass

    def schema(self):
        p = []
        for product in self.products:
            p.append(product.productname)
        return {
                "username": self.username,
                "email": self.email,
                "user_since": self.user_since,
                "teamname": self.teamname,
                "products": p,
                "active": self.active,
                "shift_start": self.shift_start,
                "shift_end": self.shift_end,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "timezone": self.timezone,
                "last_login": self.last_login,
                "admin": self.admin, 
                "in_shift": self.in_shift(),
                "team_email_notifications": self.team_email_notifications,
                "full_name": self.full_name,
                "monitor_case_updates": self.monitor_case_updates
            }
    
    # returns name of the one product that this user supports with most cases so far
    def most_product_cases(self):
        dict_product_count = {}
        for product in self.products:
            dict_product_count[product.productname] = product.product_case_count()
        if dict_product_count:
            return max(dict_product_count, key=dict_product_count.get)
        else:
            return None
    
    # converts dt into users timezone datetime string
    def user_datetime(self, dt):
        '''
        dt is the timezone aware datetime object
        returns a timezone aware datetime object in user's timezone
        '''
        return dt.astimezone(pytz.timezone(self.timezone)).strftime('%d/%b/%Y %H:%M')

    # converts dt into users timezone datetime timezone aware object
    def user_datetime_object(self, dt):
        '''
        dt is the timezone aware datetime object
        returns a timezone aware datetime object in user's timezone
        '''
        return dt.astimezone(pytz.timezone(self.timezone))
    
class Team(db.Model):
    teamname = db.Column(db.String(200), primary_key=True)
    users = db.relationship('User', backref='team', lazy=True)
    email = db.Column(db.String(200), nullable=True)
    mswebhook = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"Team'{self.teamname}', '{self.users}'"

    def update(self, d):
        if d.get('email') == "":
            self.email = None
        elif d.get('email') is not None:
            self.email = d.get('email')
        if d.get('mswebhook') == "" or d.get('mswebhook') is not None:
            self.mswebhook = d.get('mswebhook')
        return self.schema()
    
    def get_user_names(self, object=False):
        '''
        returns list of user objects or user names belonging to a team
        '''
        users_l = self.users
        if object:
            return users_l
        users = []
        for user in users_l:
            users.append(user.username)
        return users
    
    def schema(self):
        u = []
        for user in self.users:
            u.append(user.username)
        return {
            "teamname": self.teamname,
            "users": u,
            "email": self.email,
            "mswebhook": self.mswebhook
        }

class Jobs(db.Model):
    number = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.String(200))
    username = db.Column(db.ForeignKey('user.username', ondelete='SET NULL'))
    job_type = db.Column(db.String(100))
    details = db.Column(db.String(500))
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(100))

    def __repr__(self):
        return f"Job'{self.id}', '{self.job_type}', '{self.status}'"
    
    @classmethod
    def active_jobs(cls):
        l_status = [
            "Scheduled",
            "Rescheduled"
        ]
        return cls.query.filter(cls.status.in_(l_status)).all()

    @classmethod
    def search_active_job(cls, jobid):
        l_status = [
            "Scheduled",
            "Rescheduled"
        ]
        return cls.query.filter(cls.status.in_(l_status)).filter_by(id=jobid).first()
    
    def schema(self):
        return {
            "number": self.number,
            "job_id": self.id,
            "username": self.username, 
            "job_type": self.job_type, 
            "details": self.details, 
            "status": self.status,
            "time": self.time
        }
    
class Product(db.Model):
    productname = db.Column(db.String(200), primary_key=True)
    strategy = db.Column(db.String(10), default='s1')
    max_days = db.Column(db.Integer, default=2)
    max_days_month = db.Column(db.Integer, default=300)
    case_regex = db.Column(db.String(200), default='^[0-9]{4}-[0-9]{4}-[0-9]{6}$')
    quota_over_days = db.Column(db.Integer, default=1)
    sf_api = db.Column(db.String(2000), nullable=True)
    sf_job_cron = db.Column(db.String(200), nullable=True)
    sf_job_timezone = db.Column(db.String(200), nullable=True)
    sf_job_query_interval = db.Column(db.Integer, nullable=True)
    sf_product_series = db.Column(db.String(2000), nullable=True)
    sf_platform = db.Column(db.String(2000), nullable=True)
    sf_mist_product = db.Column(db.String(2000), nullable=True)
    sf_enabled = db.Column(db.Boolean, default=False)
    sf_init_email_name = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"Product'{self.productname}', '{self.strategy}', '{self.max_days}',\
                 '{self.max_days_month}', '{self.case_regex}'"

    # returns product object whose product_series matches its list
    @classmethod
    def find_product_series(cls, product_series, mist_product):
        products = Product.query.all()
        for product in products:
            if mist_product == product.sf_mist_product and product_series in product.get_product_series_list():
                return product
        for product in products:
            if product_series in product.get_product_series_list():
                return product
        return None

        #     if product_series in product.get_product_series_list():
        #         if mist_product and product.sf_mist_product not in [None, ""]:
        #             if mist_product == product.sf_mist_product:
        #                 return product
        #             else:
        #                 return None
        #         return product
        # return None

    def get_users_fullname(self):
        l_users_fullname = []
        for user in self.supported_by:
            l_users_fullname.append(user.full_name)
        return l_users_fullname

    def get_product_series_list(self):
        if self.sf_product_series:
            li = self.sf_product_series.split(',') 
            # remove spaces from all elements
            return [element.strip() for element in li]
        else:
            return []
    
    def get_platform_list(self):
        if self.sf_platform:
            li = self.sf_platform.split(',') 
            # remove spaces from all elements
            return [element.strip() for element in li]
        else:
            return []
    
    def update(self, d_product):
        self.strategy = d_product.get('strategy') or self.strategy
        self.max_days = d_product.get('max_days') or self.max_days
        self.max_days_month = d_product.get('max_days_month') or self.max_days_month
        self.case_regex = d_product.get('case_regex') or self.case_regex
        self.quota_over_days = d_product.get("quota_over_days") or self.quota_over_days
        if d_product.get("sf_api") == "" or d_product.get("sf_api") is not None:
            self.sf_api = d_product.get("sf_api")
        if d_product.get('sf_enabled') is not None:
            self.sf_enabled = d_product.get('sf_enabled')  
        self.sf_job_cron = d_product.get("sf_job_cron") or self.sf_job_cron
        self.sf_job_timezone = d_product.get("sf_job_timezone") or self.sf_job_timezone
        self.sf_job_query_interval = d_product.get("sf_job_query_interval") or self.sf_job_query_interval
        self.sf_product_series = d_product.get("sf_product_series") or self.sf_product_series
        if d_product.get("sf_init_email_name") == "" or d_product.get("sf_init_email_name") is not None:
            self.sf_init_email_name = d_product.get("sf_init_email_name")
        else:
            self.sf_init_email_name = None
        if d_product.get("sf_platform") == "" or d_product.get("sf_platform") is not None:
            self.sf_platform = d_product.get("sf_platform")
        if d_product.get("sf_mist_product") == "" or d_product.get("sf_mist_product") is not None:
            self.sf_mist_product = d_product.get("sf_mist_product")
        return self.schema()
    
    def schema(self):
        u = []
        for user in self.supported_by:
            u.append(user.username)
        return {
            "productname": self.productname,
            "strategy": self.strategy, 
            "max_days": self.max_days, 
            "max_days_month": self.max_days_month, 
            "supported_by": u,
            "case_regex": self.case_regex,
            "quota_over_days": self.quota_over_days,
            "sf_api": self.sf_api,
            "sf_job_cron": self.sf_job_cron,
            "sf_job_timezone": self.sf_job_timezone,
            "sf_job_query_interval": self.sf_job_query_interval,
            "sf_product_series": self.sf_product_series,
            "sf_platform": self.sf_platform,
            "sf_enabled": self.sf_enabled,
            "sf_init_email_name": self.sf_init_email_name,
            "sf_mist_product": self.sf_mist_product
        }
    
    # returns list of all product names
    @classmethod
    def product_names(cls):
        p = []
        products = cls.query.all()
        for product in products:
            p.append(product.productname)
        return p
    
    # returns count of cases for a product
    def product_case_count(self): 
        cases = Cases.query.filter_by(product=self.productname).all()
        return len(cases)

class Audit(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user = db.Column(db.ForeignKey('user.username', ondelete='SET NULL'))
    task_type = db.Column(db.String(100))
    task = db.Column(db.String(5000))
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Audit'{self.time}', '{self.task_type}'"
    
    def schema(self):
        return {
            "audit_id": self.id,
            "user": self.user, 
            "task_type": self.task_type, 
            "task": self.task, 
            "time": self.time
        }

class SalesforceEmails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50), db.ForeignKey('user.username'))
    email_name = db.Column(db.String(200), nullable=False, unique=True)
    email_body = db.Column(db.String(5000), nullable=True)
    email_subject = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'SalesforceEmails({self.user, self.email_name})'
    
    def update(self, d_sf_email):
        self.email_body = d_sf_email.get('email_body') or self.email_body
        self.email_subject = d_sf_email.get('email_subject') or self.email_subject

    def schema(self):
        return {
            "id": self.id,
            "user": self.user,
            "email_name": self.email_name,
            "email_body": self.email_body,
            "email_subject": self.email_subject
        }
    
    @classmethod
    def sf_all_available_email_names(cls):
        l_usernames = [current_user.username, 'admin', 'scheduler']
        emails = cls.query.filter(SalesforceEmails.user.in_(l_usernames)).all()
        l_email_names = []
        for email in emails:
            l_email_names.append(email.email_name)
        return l_email_names

class SalesforceCases(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # case_id = db.Column(db.String(50), unique=True)
    case_id = db.Column(db.String(50), unique=False)
    product = db.Column(db.String(200), db.ForeignKey('product.productname'), nullable=False)
    priority = db.Column(db.String(10))
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'SalesforceCases({self.case_id, self.product, self.priority, self.time})'
    
    @classmethod
    def add_case(cls, case_d):
        if cls.query.filter_by(case_id=case_d.get('case_id')).first():
            return None
        return cls(case_id=case_d.get('case_id'), product=case_d.get('product'), priority=case_d.get('priority'))

    @classmethod
    def case_exists(cls, case_id):
        return True if cls.query.filter_by(case_id=case_id).first() else False
    
    def schema(self):
        return {
            "case_id": self.case_id,
            "product": self.product,
            "priority": self.priority,
            "time": self.time
        }

    # get list of cases based on the arguments specified. productname is a list of productnames
    @classmethod
    def get_cases(cls, days=0, productnames=None):
        if productnames == [] or productnames == None:
            li_cases = []
        else:
            l_date = date.today()
            f_date = date.today() - timedelta(days=days)
            li_cases = cls.query.filter(func.date(cls.time).between(f_date, l_date)).\
                filter(SalesforceCases.product.in_(productnames)).order_by(SalesforceCases.time.desc()).all()
        return li_cases

class SalesforceApiRequests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(1000))
    response = db.Column(db.String(1000))
    details = db.Column(db.String(1000))
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @classmethod
    def add(cls, d_api_details):
        api_details = cls(url=d_api_details.get('url'), response=d_api_details.get('response'), details=d_api_details.get('details'))
        return api_details
    
    def schema(self):
        return {
            "id" : self.id,
            "url" : self.url,
            "details" : self.details,
            "time" : self.time
        }

    # Returns the number of api requests made in last 'days' days
    @classmethod
    def number_of_requests(cls, days=1):
        f_date = datetime.utcnow().date() - timedelta(days=days)
        l_date = datetime.utcnow().date()
        li_cases = cls.query.filter(func.date(cls.time).between(f_date, l_date)).all()
        return li_cases

    @classmethod
    def add_user(cls, d):
        pwd_hash = cls.get_hash(d.get('password'))
        user = cls(username=d.get('username'), email=d.get('email'), password=pwd_hash, teamname=d.get('teamname'), 
                active=d.get('active'), shift_start=d.get('shift_start'), shift_end=d.get('shift_end'), 
                timezone=d.get('timezone'), admin=d.get('admin'), team_email_notifications=d.get('team_email_notifications'),
                first_name=d.get('first_name'), last_name=d.get('last_name'), monitor_case_updates=d.get('monitor_case_updates'))
        return user
    
class Cases(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    user = db.Column(db.String(50), db.ForeignKey('user.username'), nullable=False)
    product = db.Column(db.String(200), db.ForeignKey('product.productname'), nullable=False)
    # user = db.Column(db.String(50), db.ForeignKey('user.username', ondelete="CASCADE"))
    # product = db.Column(db.String(200), db.ForeignKey('product.productname', ondelete="CASCADE"))
    time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comments = db.Column(db.String(300))
    mode = db.Column(db.String(50), default="auto")
    priority = db.Column(db.String(10))
    # I tried to set on delete to default but it kept failing at foreign key constrain check. For now i have changed
    # it to on delete set null. A user deletion can skew the cases data with this approach.
    assigned_by = db.Column(db.String(50), db.ForeignKey('user.username', ondelete="SET Null"), default="admin")
    sf_account_name = db.Column(db.String(2000), nullable=True)
    assignment_history = db.Column(db.String(2000), nullable=True)

    def __repr__(self):
        return f'Case({self.id, self.user , self.product, self.time, self.sf_account_name})'

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    # check if a case exists. return true if it does else return false
    @classmethod
    def case_exists(cls, case_id):
        return True if cls.query.filter_by(id=case_id).first() else False
    
    # WITHOUT PAGINATION
    # if only user name is passed, retuns list of all cases assigned to a user 
    # f_date and l_date are datetime.date objects in UTC. This is because all datetime type columns in database store datesin UTC zone.
    # if f_date is passed, returns list of cases between f_date and today
    # if f_date and l_date is passed, returns list of cases between f_date and l_date
    # if p_name is passed, returns list of cases for only that product
    @classmethod
    def get_all_cases_of_user(cls, u_name, f_date=None, l_date=None, p_name=None):
        if f_date==None and l_date==None:
            if p_name == None:
                li_cases = cls.query.filter_by(user=u_name).order_by(Cases.time.desc()).all()
            else:
                li_cases = cls.query.filter_by(user=u_name, product=p_name).order_by(Cases.time.desc()).all()
        else:
            if l_date==None:
                l_date = date.today()
            if p_name == None:
                li_cases = cls.query.filter_by(user=u_name).filter(func.date(cls.time).between(f_date, l_date)).order_by(Cases.time.desc()).all()
            else:
                li_cases = cls.query.filter_by(user=u_name, product=p_name).filter(func.date(cls.time).between(f_date, l_date)).order_by(Cases.time.desc()).all()
        return li_cases

    # THE BELOW IS SAME METHOD AS ABOVE BUT HAS PAGINATION
    # if only user name is passed, retuns list of all cases assigned to a user 
    # f_date and l_date are datetime.date objects in UTC. This is because all datetime type columns in database store datesin UTC zone.
    # if f_date is passed, returns list of cases between f_date and today
    # if f_date and l_date is passed, returns list of cases between f_date and l_date
    # if p_name is passed, returns list of cases for only that product
    # page is used for pagination
    @classmethod
    def get_cases_of_user(cls, u_name, f_date=None, l_date=None, p_name=None, page=1, per_page=10):
        if f_date==None and l_date==None:
            if p_name == None:
                li_cases = cls.query.filter_by(user=u_name).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
            else:
                li_cases = cls.query.filter_by(user=u_name, product=p_name).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
        else:
            if l_date==None:
                l_date = date.today()
            if p_name == None:
                li_cases = cls.query.filter_by(user=u_name).filter(func.date(cls.time).between(f_date, l_date)).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
            else:
                li_cases = cls.query.filter_by(user=u_name, product=p_name).filter(func.date(cls.time).between(f_date, l_date)).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
        return li_cases

    # if only user name is passed, retuns list of all cases assigned by that user 
    # f_date and l_date are datetime.date objects in UTC. This is because all datetime type columns in database store datesin UTC zone.
    # if f_date is passed, returns list of cases between f_date and today
    # if f_date and l_date is passed, returns list of cases between f_date and l_date
    # page is used for pagination
    @classmethod
    def get_cases_assigned_by_user(cls, u_name, f_date=None, l_date=None, page=1, per_page=10):
        if f_date==None and l_date==None:
            li_cases = cls.query.filter_by(assigned_by=u_name).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
        else:
            if l_date==None:
                l_date = date.today()
            li_cases = cls.query.filter_by(assigned_by=u_name).filter(func.date(cls.time).between(f_date, l_date)).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
        return li_cases
    
    # if only product name is passed, retuns list of all cases of that product
    # f_date and l_date are datetime.date objects in UTC. This is because all datetime type columns in database store datesin UTC zone.
    # if f_date is passed, returns list of cases between f_date and today
    # if f_date and l_date is passed, returns list of cases between f_date and l_date
    # page is used for pagination
    @classmethod
    def get_cases_of_product(cls, p_name, f_date=None, l_date=None, page=1, per_page=10):
        if f_date==None and l_date==None:
            li_cases = cls.query.filter_by(product=p_name).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
        else:
            if l_date==None:
                l_date = date.today()
            li_cases = cls.query.filter_by(product=p_name).filter(func.date(cls.time).between(f_date, l_date)).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
        return li_cases

    # if only team name is passed, retuns list of all cases owned by users supporting that product
    # f_date and l_date are datetime.date objects in UTC. This is because all datetime type columns in database store datesin UTC zone.
    # if f_date is passed, returns list of cases between f_date and today
    # if f_date and l_date is passed, returns list of cases between f_date and l_date
    # page is used for pagination
    @classmethod
    def get_cases_of_team(cls, t_name=None, f_date=None, l_date=None, page=1, mode=None, priority=None, per_page=10):
        if t_name:
            users = Team.query.filter_by(teamname=t_name).first().users
        else:
            users = User.query.all()
        l_usernames = []
        for user in users:
            l_usernames.append(user.username)
        if f_date==None and l_date==None:
            if mode and priority:
                l_cases = cls.query.filter(Cases.user.in_(l_usernames)).filter_by(mode=mode).filter_by(priority=priority).\
                    order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
            elif mode:
                l_cases = cls.query.filter(Cases.user.in_(l_usernames)).filter_by(mode=mode).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
            elif priority:
                l_cases = cls.query.filter(Cases.user.in_(l_usernames)).filter_by(priority=priority).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
            else:
                l_cases = cls.query.filter(Cases.user.in_(l_usernames)).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
        else:
            if l_date==None:
                l_date = date.today()
            if mode and priority:
                l_cases = cls.query.filter(Cases.user.in_(l_usernames)).filter(func.date(cls.time).between(f_date, l_date)).\
                filter_by(mode=mode).filter_by(priority=priority).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
            elif mode:
                l_cases = cls.query.filter(Cases.user.in_(l_usernames)).filter(func.date(cls.time).between(f_date, l_date)).\
                    filter_by(mode=mode).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
            elif priority:
                l_cases = cls.query.filter(Cases.user.in_(l_usernames)).filter(func.date(cls.time).between(f_date, l_date)).\
                    filter_by(priority=priority).order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
            else:
                l_cases = cls.query.filter(Cases.user.in_(l_usernames)).filter(func.date(cls.time).between(f_date, l_date)).\
                    order_by(Cases.time.desc()).paginate(per_page=per_page, page=page)
        return l_cases

    def schema(self):
        return {
            "case_id": self.id,
            "assigned_to": self.user,
            "assigned_by": self.assigned_by,
            "product" : self.product,
            "time" : self.time,
            "mode" : self.mode,
            "comments" : self.comments,
            "priority" : self.priority,
            "sf_account_name" : self.sf_account_name,
            "assignment_history" : self.assignment_history
        }