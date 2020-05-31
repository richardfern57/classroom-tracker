# pylint: disable=no-member
from .api import GoogleApiConnector


class SheetsConnector(GoogleApiConnector):

    _scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    _service = 'sheets'
    _version = 'v4'

    def get_data(self, spreadsheet_id, range):
        """Load data from a specified spreadsheet and range

        Parameters
        ----------
        spreadsheet_id : str
            The ID of the google spreadsheet
        range : str
            The range of data to access, such as 'Sheet1!A2:B3'

        Returns
        -------
        list of list of str
            The data as a list where each sub-list is a row and each string is
            a cell's contents
        """
        return (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range)
            .execute()
            .get('values', [])
        )
