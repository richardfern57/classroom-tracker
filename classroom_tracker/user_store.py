import pandas
import difflib
import functools

from . import google_api


class UserStore:
    """A store for classrooms user details"""

    def __init__(self, spreadsheet_id, course_id):
        self.classrooms = google_api.ClassroomConnector(
            credentials_file='classrooms.json',
            token_file='classrooms.pkl')

        self.sheets = google_api.SheetsConnector(
            credentials_file='sheets.json',
            token_file='sheets.pkl')

        self.spreadsheet_id = spreadsheet_id

        self.mappings = self.sheets.get_data(
            self.spreadsheet_id,
            'user_mappings')

        self.cached_users = (
            self.classrooms.get_students(course_id)
            .assign(
                formatted_name=lambda d:
                    d['last_name'] + ', ' + d['first_name'])
        )

    def get_emails(self, user_ids):
        """Get the email addresses for the users

        Parameters
        ----------
        user_ids : pandas.Series
            A series of user_ids

        Returns
        -------
        pandas.Series
            A series of email addresses with a semi-colon appended
        """
        return user_ids.map(self.cached_users['email'])

    def get_names(self, user_ids):
        """Get the formatted names relating to the user_ids. In case the name
        cannot be matched with one found in the user_mappings sheet, simply
        return the formatted_name found in google, accompanied by (???)

        Parameters
        ----------
        user_ids : pandas.Series
            A series of user_ids

        Returns
        -------
        pandas.Series
            A series of formatted names
        """
        names = self.mappings['formatted_name']
        match_names = [name.lower().replace(',', '') for name in names]
        lookup = pandas.Series(names.tolist(), index=match_names)

        @functools.lru_cache()
        def get_close_name(name):
            match_name = name.lower().replace(',', '')
            match = difflib.get_close_matches(match_name, match_names, n=1)
            return lookup[match[0]] if len(match) > 0 else f'{name} (???)'

        return (
            user_ids
            .map(self.cached_users['formatted_name'])
            .apply(get_close_name)
        )

    def get_groups(self, user_ids, target='form'):
        """Get the groups for a series of users

        Parameters
        ----------
        user_ids : pandas.Series
            A series of user_ids

        Returns
        -------
        pandas.Series
            A series of groups
        """
        mappings = self.mappings.set_index('formatted_name')['group']
        return self.get_names(user_ids).map(mappings).fillna('???')
