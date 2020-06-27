# pylint: disable=no-member
import pandas

from .api import GoogleApiConnector


class ClassroomConnector(GoogleApiConnector):
    """Connector to the Google Classrooms API"""

    _scopes = [
        'https://www.googleapis.com/auth/classroom.courses.readonly',
        'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
        'https://www.googleapis.com/auth/classroom.rosters.readonly',
        'https://www.googleapis.com/auth/classroom.profile.emails'
    ]
    _service = 'classroom'
    _version = 'v1'

    def get_courses(self):
        """Get all the courses

        Returns
        -------
        pandas.DataFrame
            A dataframe of courses indexed by course_id, with columns
            course_name
        """
        courses = (
            self.service
            .courses()
            .list()
            .execute()
            .get('courses', [])
        )

        index = pandas.Index(
            [course['id'] for course in courses],
            name='course_id')

        return pandas.DataFrame(
            [[course['name']] for course in courses],
            index=index,
            columns=['course_name'])

    def get_courseworks(self, course_id):
        """Get all the courseworks for a particular course

        Parameters
        ----------
        course_id : int
            The id of the course to query

        Returns
        -------
        pandas.DataFrame
            A dataframe of courseworks indexed by coursework_id with columns
            title
        """
        courseworks = (
            self.service
            .courses()
            .courseWork()
            .list(courseId=course_id)
            .execute()
            .get('courseWork', [])
        )

        index = pandas.Index(
            [coursework['id'] for coursework in courseworks],
            name='coursework_id')

        return pandas.DataFrame(
            [[coursework['title']] for coursework in courseworks],
            index=index,
            columns=['coursework_name'])

    @staticmethod
    def _parse_turn_in(submission):
        """Parse the submission data to retrieve the turn-in time, if
        applicable

        Parameters
        ----------
        submission : dict
            A submission object

        Returns
        -------
        pandas.Timestamp
            A timestamp for the last turn-in action
        """
        history = submission.get('submissionHistory', [])
        history = [
            item.get('stateHistory', {'state': None}) for item in history]
        history = [item for item in history if item['state'] == 'TURNED_IN']
        times = [
            pandas.Timestamp(turn_in['stateTimestamp'])
            for turn_in in history]

        if len(times) > 0:
            return max(times)
        else:
            return pandas.NaT

    def get_submissions(self, course_id, coursework_id):
        """Get all submissions for a particular piece of coursework within a
        particular course

        Parameters
        ----------
        course_id : int
            The id of the course
        coursework_id : int
            The id of the coursework

        Returns
        -------
        pandas.DataFrame
            A dataframe of submissions
        """
        submissions = (
            self.service
            .courses()
            .courseWork()
            .studentSubmissions()
            .list(courseId=course_id, courseWorkId=coursework_id)
            .execute()
            .get('studentSubmissions', [])
        )

        index = pandas.Index(
            [submission['id'] for submission in submissions],
            name='submission_id')

        return pandas.DataFrame(
            [
                {
                    'user_id': sub['userId'],
                    'turn_in_time': self._parse_turn_in(sub),
                    'state': sub['state'],
                    'num_attachments': len(
                        sub['assignmentSubmission']
                        .get('attachments', []))}
                for sub in submissions],
            index=index)

    def get_students(self, course_id):
        """Get all the student details for a particular course

        Parameters
        ----------
        course_id : str
            The ID of the course to get details for

        Returns
        -------
        pandas.DataFrame
            The students indexed by user_id, with columns first_name,
            last_name, full_name and email
        """
        students = []
        token = {}
        while True:
            page = (
                self.service
                .courses()
                .students()
                .list(courseId=course_id, pageSize=0, **token)
                .execute()
            )
            students += page.get('students', [])

            if 'nextPageToken' in page.keys():
                token['pageToken'] = page['nextPageToken']
            else:
                break

        return (
            pandas.DataFrame(students)
            .assign(
                name=lambda d: d['profile'].str['name'],
                first_name=lambda d: d['name'].str['givenName'],
                last_name=lambda d: d['name'].str['familyName'],
                full_name=lambda d: d['name'].str['fullName'],
                email=lambda d: d['profile'].str['emailAddress']
            )
            .drop(columns=['courseId', 'profile', 'name'])
            .rename(columns={'userId': 'user_id'})
            .set_index('user_id')
        )
