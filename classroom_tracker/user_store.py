import pandas
import difflib

from . import google_api


class UserStore:
    """A store for classrooms user details"""

    def __init__(self, spreadsheet_id):
        self.classrooms = google_api.ClassroomConnector(
            credentials_file='classrooms.json',
            token_file='classrooms.pkl')

        self.sheets = google_api.SheetsConnector(
            credentials_file='sheets.json',
            token_file='sheets.pkl')

        self.spreadsheet_id = spreadsheet_id
        self.cached_users = (
            self.sheets.get_data(self.spreadsheet_id, 'user_ids')
            .assign(user_id=lambda d: d['user_id'])
            .set_index('user_id')
        )
        self.mappings = self.sheets.get_data(
            self.spreadsheet_id,
            'user_mappings')

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
        lookup = pandas.Series(names, index=match_names)

        def get_close_name(name):
            match_name = name.lower().replace(',', '')
            match = difflib.get_close_matches(match_name, match_name, n=1)
            return lookup[match[0]] if len(match) > 0 else f'{name} (???)'

        return (
            user_ids
            .apply(lambda i: self.get_user(i)['formatted_name'])
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

    def get_user(self, user_id):
        """Get the details of a particular user

        Parameters
        ----------
        user_id : int
            The ID of the user

        Returns
        -------
        pandas.Series
            A series of data about the user including first_name, last_name,
            full_name and formatted_name
        """
        if user_id not in self.cached_users.index:
            self.cached_users = self.cached_users.append(
                self.classrooms.get_user(user_id)
                .assign(
                    formatted_name=lambda d:
                        d['last_name'] + ', ' + d['first_name'])
            )
            self.save()

        return self.cached_users.loc[user_id]

    def save(self):
        """Save the current cache of users to the spreadsheet"""
        self.sheets.write_data(
            self.spreadsheet_id,
            'user_ids!A2',
            self.cached_users.reset_index().values.tolist())
