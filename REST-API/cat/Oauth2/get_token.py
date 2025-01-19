import requests
from flask import current_app

class OAuth2Client:
    def __init__(self, client_id, client_secret, username, password, url, grant_type):
        self.access_token = None
        self.grant_type = grant_type
        self.name = "cat_token"
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token_url = url
        self.username = username
        self.password = password

        self.get_access_token()

    def get_access_token(self):
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        data = f'client_id={self.client_id}&client_secret={self.client_secret}&grant_type={self.grant_type}&username={self.username}&password={self.password}'
        response = requests.post(self.access_token_url, data=data, headers=headers)
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
        else:
            current_app.logger.error(f"Failed to fetch token from {self.access_token_url}. {response.status_code} : {response}")

