# pylint: disable=no-member
import os
import pickle
import logging
import googleapiclient.discovery
import google_auth_oauthlib.flow
import google.auth.transport.requests


class GoogleApiAccessError(Exception):
    """An exception relating to accessing a google API"""


class GoogleApiConnector:

    _scopes = []
    _service = None
    _version = None

    def __init__(self, token_file=None, credentials_file=None):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.token_file = token_file or os.environ.get(
            f'{self._service}_token_file',
            'token.pkl')

        self.credentials_file = credentials_file or os.environ.get(
            f'{self._service}_credentials_file',
            'credentials.json')

        if os.path.exists(self.token_file):
            self.load_token()
        else:
            self.logger.warning('Token not found. Generating from credentials')
            self.generate_token()
            self.save_token()

        self.service = googleapiclient.discovery.build(
            self._service,
            self._version,
            credentials=self.token)

    def load_token(self):
        """Load a picked Google Sheets access token"""
        with open(self.token_file, 'rb') as token:
            self.token = pickle.load(token)

        self.token.refresh(google.auth.transport.requests.Request())

        if not self.token.valid:
            self.logger.warning('Token invalid. Generating a new one')
            self.generate_token()

    def generate_token(self):
        """Generate a new Google Sheets access token"""
        if not os.path.exists(self.credentials_file):
            raise GoogleApiAccessError(
                f'No access token or credentials found for {self._service}. '
                f'Specify the file locations with environment variables '
                f'{self._service}_token_file or sheets_credentials_file. '
                f'Alternatively, place at token.pkl or credentials.json')

        self.token = (
            google_auth_oauthlib.flow.InstalledAppFlow
            .from_client_secrets_file(self.credentials_file, self._scopes)
            .run_local_server(port=0)
        )

    def save_token(self):
        """Pickle the Google Sheets access token"""
        with open(self.token_file, 'wb') as token:
            pickle.dump(self.token, token)
