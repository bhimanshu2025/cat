from simple_salesforce import Salesforce, exceptions
from soql import attributes
from soql import load_models_from_salesforce_data
from soql import Model
from soql import select
from cat import api_utils
from flask import current_app
import requests
from datetime import datetime, timedelta
from cat.models import SalesforceApiRequests

def audit_queries(func):
    def wrapper(*args, **kwargs):
        # current_app.logger.info(f"func name is {func.__name__} and aregs are {args} AND {kwargs}")
        url = current_app.config['SF_INSTANCE_URL']
        details = {
            "Function Name": func.__name__,
            "args": args,
            "kwargs": kwargs
        }
        sf_api = SalesforceApiRequests(url=url, details=str(details))
        api_utils.add_all([sf_api])
        return func(*args, **kwargs)
    return wrapper

class Case(Model):
        case_owner = attributes.String('CEC_Case_Owner__c', nullable=True)
        account_name = attributes.String('CEC_Account_Name__c', nullable=True)
        subject = attributes.String('Subject', nullable=True)
        created_date = attributes.String('CreatedDate', nullable=True)
        case_id = attributes.String('CaseNumber', nullable=True)
        status = attributes.String('CEC_Status__c', nullable=True)
        product_series = attributes.String('CEC_ProductSeries__c', nullable=True)
        platform = attributes.String('CEC_Platforms__c', nullable=True)
        priority = attributes.String('Priority', nullable=True)
        last_external_update_email = attributes.String('CEC_Last_Public_Poster_Email__c', nullable=True)
        last_external_update_utc_time = attributes.String('CEC_Last_Update_Date_Time_UTC__c', nullable=True)
        last_external_update_note = attributes.String('CEC_Last_Public_Note__c', nullable=True)
        mist_case = attributes.Boolean('CEC_Mist_Case__c', nullable=True)
        mist_product = attributes.String('CEC_Mist_Product__c', nullable=True)
    # def convert_create_date_to_user_timezone(self):
    #     created_data = current_user.user_datetime()

class SFCases(object):
    def __init__(self, instance_url=None):
        self.instance_url = instance_url
        self._init_sf_session()

    def _init_sf_session(self):
        if current_app.sf_token is None: 
            current_app.sf_token = self._get_token()
        try:
            self.sf = Salesforce(instance_url=self.instance_url, session_id=current_app.sf_token)
        except TypeError as err:
            current_app.logger.error(f"Failed to connect to Salesforce. Salesforce URL not found. {err}")
            self.sf = None

    # @audit_queries
    def _get_token(self):
        return api_utils.get_sf_token()
    
    @audit_queries
    def get_case_details(self, case_id = None):
        # Incase the sf object is not initialized, exit
        if self.sf == None:
            return 500
        if case_id:
            if current_app.case_cache.search(case_id):
                return current_app.case_cache.search(case_id)
            else:
                try:
                    query = select(Case).where(Case.case_id==case_id)
                    resp = self.sf.query(str(query))
                    if resp.get('totalSize') == 0:
                        return None
                    else: 
                        current_app.case_cache.add(case_id, load_models_from_salesforce_data(resp)[0])
                        return load_models_from_salesforce_data(resp)[0]
                except requests.exceptions.ConnectionError as err:
                    current_app.logger.error(f'Failed to connect to Salesforce Server. {err}')
                    return 500
                except exceptions.SalesforceExpiredSession as err:
                    current_app.logger.error(f'Salesforce Session Expired. {err}')
                    current_app.sf_token = None
                    self._init_sf_session()
                    return self.get_case_details(case_id)
    
    @audit_queries
    def get_open_cases_of_users(self, users_list=[]):
        # Incase the sf object is not initialized, exit
        if self.sf == None:
            return 500
        if users_list == []:
            return None
        query = select(Case).where(Case.case_owner.in_(users_list)).where(Case.status != 'Closed')
        try:
            resp = self.sf.query(str(query))
            if resp.get('totalSize') == 0:
                return None
            else: 
                current_app.logger.debug(f'Fetching cases for following list of users : {users_list}')
                current_app.logger.debug(f'List of cases fetched from Salesforce : {load_models_from_salesforce_data(resp)[0]}')
                return load_models_from_salesforce_data(resp)
        except requests.exceptions.ConnectionError as err:
            current_app.logger.error(f'Failed to connect to Salesforce Server. {err}')
            return 500
        except exceptions.SalesforceExpiredSession as err:
            current_app.logger.error(f'Salesforce Session Expired. {err}')
            current_app.sf_token = None
            self._init_sf_session()
            return self.get_open_cases_of_users(users_list)

    @audit_queries
    def get_open_cases_of_accounts(self, account_name_list=[]):
        # Incase the sf object is not initialized, exit
        if self.sf == None:
            return 500
        query = select(Case).where(Case.account_name.in_(account_name_list)).where(Case.status != 'Closed').order_by(Case.product_series)
        try:
            resp = self.sf.query(str(query))
            if resp.get('totalSize') == 0:
                return None
            else: 
                current_app.logger.debug(f'Fetching cases for following list of accounts : {account_name_list}')
                current_app.logger.debug(f'List of cases fetched from Salesforce : {load_models_from_salesforce_data(resp)[0]}')
                return load_models_from_salesforce_data(resp)
        except requests.exceptions.ConnectionError as err:
            current_app.logger.error(f'Failed to connect to Salesforce Server. {err}')
            return 500
        except exceptions.SalesforceExpiredSession as err:
            current_app.logger.error(f'Salesforce Session Expired. {err}')
            current_app.sf_token = None
            self._init_sf_session()
            return self.get_open_cases_of_users(account_name_list)
        
    @audit_queries
    def get_product_cases(self, product_series=[], platform=[], mist_product=[], days=0, hours=0, minutes=0, seconds=15):
        # Incase the sf object is not initialized, exit
        if self.sf == None:
            return 500
        # tz_aware_dt_utc = (datetime.utcnow().astimezone() - timedelta(days=days)).isoformat().replace("+00:00", "Z")
        # By default keep an offset of 15s 
        tz_aware_dt_utc = (datetime.utcnow().astimezone() - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds))
        if mist_product:
            if product_series and platform:
                query = select(Case).where(Case.product_series.in_(product_series)).where(Case.platform.in_(platform)).\
                    where(Case.mist_product.in_(mist_product)).where(Case.created_date > tz_aware_dt_utc)
            elif product_series:
                query = select(Case).where(Case.product_series.in_(product_series)).\
                    where(Case.mist_product.in_(mist_product)).where(Case.created_date > tz_aware_dt_utc)
            elif platform:
                query = select(Case).where(Case.platform.in_(platform)).\
                    where(Case.mist_product.in_(mist_product)).where(Case.created_date > tz_aware_dt_utc)
            else: 
                return None
        else:
            if product_series and platform:
                query = select(Case).where(Case.product_series.in_(product_series)).where(Case.platform.in_(platform)).\
                    where(Case.created_date > tz_aware_dt_utc)
            elif product_series:
                query = select(Case).where(Case.product_series.in_(product_series)).where(Case.created_date > tz_aware_dt_utc)
            elif platform:
                query = select(Case).where(Case.platform.in_(platform)).where(Case.created_date > tz_aware_dt_utc)
            else: 
                return None
        try:
            resp = self.sf.query(str(query))
            if resp.get('totalSize') == 0:
                return None
            else: 
                current_app.logger.debug(f'Fetching cases for following list of product series : {product_series}, mist_product : \
                                         {mist_product} and platforms {platform} in past days {days}, hours {hours}, minutes {minutes}')
                current_app.logger.debug(f'List of cases fetched from Salesforce : {load_models_from_salesforce_data(resp)[0]}')
                return load_models_from_salesforce_data(resp)
        except requests.exceptions.ConnectionError as err:
            current_app.logger.error(f'Failed to connect to Salesforce Server. {err}')
            return 500
        except exceptions.SalesforceExpiredSession as err:
            current_app.logger.error(f'Salesforce Session Expired. {err}')
            current_app.sf_token = None
            self._init_sf_session()
            return self.get_product_cases(product_series=product_series, platform=platform, days=days, hours=hours, minutes=minutes,
                                           seconds=seconds)
