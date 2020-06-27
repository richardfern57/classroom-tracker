import pandas
import googleapiclient.errors

from . import user_store
from . import google_api


class Tracker:
    """A class of utility methods for tracking classrooms submissions"""

    def __init__(self, spreadsheet_id):
        self.classrooms = google_api.ClassroomConnector(
            credentials_file='classrooms.json',
            token_file='classrooms.pkl')

        self.sheets = google_api.SheetsConnector(
            credentials_file='sheets.json',
            token_file='sheets.pkl')

        self.spreadsheet_id = spreadsheet_id

    def upload_all_submissions(self, course_ids=[]):
        """Upload the submissions data for all the course_ids listed

        Parameters
        ----------
        course_ids : list of str, optional
            A list of the course_ids, by default []
        """
        courses = self.classrooms.get_courses().loc[course_ids]
        for course_id, course in courses.groupby(level=0):
            name = course['course_name'].iloc[0]
            print('\n\n', name)

            try:
                self.sheets.get_data(self.spreadsheet_id, name)
            except googleapiclient.errors.HttpError:
                self.sheets.add_sheet(self.spreadsheet_id, name)
            except (IndexError, ValueError):
                pass

            submissions = self.get_submissions(course_id).reset_index()
            columns = [submissions.columns.tolist()]
            values = submissions.fillna('').astype(str).values.tolist()
            upload = columns + values

            self.sheets.write_data(
                self.spreadsheet_id,
                name,
                upload,
                mode='USER_ENTERED')
            print('Uploaded submissions')

    def get_submissions(self, course_id):
        """Get the submissions results for a particular course_id

        Parameters
        ----------
        course_id : str
            The ID of the course

        Returns
        -------
        pandas.DataFrame
            A dataframe indexed by group, name and metric where the column are
            the coursework names
        """
        courseworks = self.classrooms.get_courseworks(course_id)
        print('Retrieved courseworks')
        students = user_store.UserStore(self.spreadsheet_id, course_id)
        print('Retrieved students')

        submissions = pandas.concat([
            self.classrooms.get_submissions(course_id, coursework_id)
            .melt(id_vars='user_id', var_name='metric', value_name='value')
            .assign(
                course=coursework['coursework_name'].iloc[0],
                name=lambda d: students.get_names(d['user_id']),
                email=lambda d: students.get_emails(d['user_id']),
                group=lambda d: students.get_groups(d['user_id']))
            for coursework_id, coursework in courseworks.groupby(level=0)])
        print('Retrieved submissions')

        return (
            submissions
            .set_index([
                'group', 'user_id', 'name', 'email', 'metric', 'course'])
            .unstack(level='course')['value']
            .droplevel('user_id')
        )
