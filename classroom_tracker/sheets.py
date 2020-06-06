# pylint: disable=no-member
import pandas

from .api import GoogleApiConnector


class SheetsConnector(GoogleApiConnector):
    """Connector to the Google Sheets API"""

    _scopes = ['https://www.googleapis.com/auth/spreadsheets']
    _service = 'sheets'
    _version = 'v4'

    def get_data(self, spreadsheet_id, range_name):
        """Load data from a specified spreadsheet and range

        Parameters
        ----------
        spreadsheet_id : str
            The ID of the google spreadsheet
        range_name : str
            The range of data to access, such as 'Sheet1!A2:B3'

        Returns
        -------
        list of list of str
            The data as a list where each sub-list is a row and each string is
            a cell's contents
        """
        data = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
            .get('values', [])
        )

        return pandas.DataFrame(data[1:], columns=data[0])

    def write_data(self, spreadsheet_id, range_name, values, mode='RAW'):
        """Write data to a google spreadsheet

        Parameters
        ----------
        spreadsheet_id : str
            The ID of the google spreadsheet
        range_name : str
            The range of the data to write to
        values : list of list
            A two-dimensional list of objects to be written to the spreadsheet
        mode : str, optional
            The mode to use for writing, by default 'RAW', which inputs the
            values exactly as written. Alternatives include 'USER_ENTERED',
            which enters the values as though a user was entering them
        """
        assert mode in ['RAW', 'USER_ENTERED']

        result = (
            self.service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=mode,
                body={'values': values})
            .execute()
        )

        updates = result.get('updatedCells')
        self.logger.info(f'{updates} cells updated in {spreadsheet_id}')
