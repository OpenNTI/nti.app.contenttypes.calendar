#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ
from contextlib import contextmanager
from functools import partial

from hamcrest import has_item
from hamcrest import is_
from hamcrest import contains
from hamcrest import not_
from hamcrest import not_none
from hamcrest import has_entries
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_properties
from hamcrest import contains_string
from hamcrest import less_than_or_equal_to

from datetime import datetime

from zope import component
from zope import interface

from nti.app.contenttypes.calendar.tests import CalendarLayerTest

from nti.app.products.courseware.interfaces import ACT_RECORD_EVENT_ATTENDANCE
from nti.app.products.courseware.interfaces import ACT_VIEW_EVENT_ATTENDANCE

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.contenttypes.calendar.model import Calendar
from nti.contenttypes.calendar.model import CalendarEvent

from nti.coremetadata.interfaces import IContained

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.authorization import ACT_READ
from nti.dataserver.authorization import ROLE_ADMIN

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces
from nti.dataserver.authorization_acl import ace_denying_all

from nti.dataserver.interfaces import ALL_PERMISSIONS

from nti.dataserver.users import User

from nti.dataserver.users.interfaces import IProfileDisplayableSupplementalFields

from nti.externalization.externalization.standard_fields import datetime_to_string

from nti.ntiids.oids import to_external_ntiid_oid


class MockCalendar(Calendar):

    def __acl__(self):
        aces = [ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, type(self)),
                ace_denying_all()]
        acl = acl_from_aces(aces)
        return acl


class TestCalendarEventViews(CalendarLayerTest):

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def test_calendar_event_crud(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            calendar = MockCalendar(title=u"study")
            calendar.containerId = u'container_id'
            calendar.id = u'container_id'
            interface.alsoProvides(calendar, IContained)

            user = self._create_user(username)
            user.addContainedObject(calendar)

            calendar_ntiid = to_external_ntiid_oid(calendar)

        assert_that(calendar_ntiid, not_none())

        # Create
        calendar_url = '/dataserver2/Objects/%s' % calendar_ntiid

        params = {
            "MimeType": "application/vnd.nextthought.calendar.calendarevent",
            "title": "go to school",
            "description": "let us go",
            "icon": "/home/go",
            "location": "oklahoma",
            "start_time": "2018-09-20T09:00Z",
            "end_time": "2018-09-20T12:00Z"
        }
        res = self.testapp.post_json(calendar_url, params=params, status=201).json_body
        assert_that(res, has_entries({"MimeType": "application/vnd.nextthought.calendar.calendarevent",
                                      "title": "go to school",
                                      "description": "let us go",
                                      "icon": "/home/go",
                                      "location": "oklahoma",
                                      "start_time": "2018-09-20T09:00:00Z",
                                      "end_time": "2018-09-20T12:00:00Z",
                                      "Last Modified": not_none(),
                                      "NTIID": not_none()}))
        event_id = res['ID']
        event_oid = res['OID']
        event_url = '/dataserver2/Objects/%s' % event_oid

        with mock_dataserver.mock_db_trans(self.ds):
            assert_that(calendar, has_length(1))
            event = calendar.retrieve_event(event_id)
            assert_that(event, has_properties({'title': 'go to school',
                                               'description': 'let us go',
                                               'icon': '/home/go',
                                               'location': 'oklahoma',
                                               'start_time': not_none(),
                                               'end_time': not_none()}))

        # Get
        res = self.testapp.get(event_url, status=200).json_body
        assert_that(res, has_entries({"MimeType": "application/vnd.nextthought.calendar.calendarevent",
                                      "NTIID": event_oid}))
        self.require_link_href_with_rel(res, 'edit')

        # Update
        params = {
            "title": "aa",
            "description": "bb",
            "location": "OK",
            "icon": "/home/ok",
            "start_time": "2018-09-21T00:00:00Z",
            "end_time": "2018-09-22T00:00:00Z"
        }
        res = self.testapp.put_json(event_url, params=params, status=200).json_body
        assert_that(res, has_entries({"MimeType": "application/vnd.nextthought.calendar.calendarevent",
                                      "title" : "aa",
                                      "description": "bb",
                                      "location": "OK",
                                      "icon": "/home/ok",
                                      "start_time": "2018-09-21T00:00:00Z",
                                      "end_time": "2018-09-22T00:00:00Z"}))

        # Deletion
        self.testapp.delete(event_url, status=204)
        with mock_dataserver.mock_db_trans(self.ds):
            assert_that(calendar, has_length(0))


class TestCalendarViews(CalendarLayerTest):

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def test_sorting(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            calendar = MockCalendar(title=u"study")
            calendar.containerId = u'container_id'
            calendar.id = u'container_id'
            interface.alsoProvides(calendar, IContained)

            user = self._create_user(username)
            user.addContainedObject(calendar)

            calendar_ntiid = to_external_ntiid_oid(calendar)
            assert_that(calendar_ntiid, not_none())

        with mock_dataserver.mock_db_trans(self.ds):
            for title, description, location, start_time, end_time in (
                                                                    (u"aa", u"d", u"A2", datetime(2018, 10, 23), datetime(2018, 11, 23, 0, 0, 0)),
                                                                    (u"b1", u"c", u"a", datetime(2018, 10, 25), datetime(2018, 11, 19, 0, 0, 0)),
                                                                    (u"AAA", None, None, datetime(2018, 10, 22), datetime(2018, 11, 24, 0, 0, 0)),
                                                                    (u'B', u'DD', u"e", datetime(2018, 10, 24), None)):
                event = CalendarEvent(title=title,
                                      description=description,
                                      location=location,
                                      icon=u'/home/nt',
                                      start_time=start_time,
                                      end_time=end_time)
                calendar.store_event(event)

        calendar_url = '/dataserver2/Objects/%s/@@contents' % calendar_ntiid
        res = self.testapp.get(calendar_url, params={'sortOn': 'title', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('aa', 'AAA', 'B', 'b1'))

        res = self.testapp.get(calendar_url, params={'sortOn': 'description', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that([x['description'] for x in res['Items']], contains(None, 'c', 'd', 'DD'))

        res = self.testapp.get(calendar_url, params={'sortOn': 'location', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that([x['location'] for x in res['Items']], contains(None, 'a', 'A2', 'e'))

        res = self.testapp.get(calendar_url, params={'sortOn': 'start_time', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('AAA', 'aa', 'B', 'b1'))

        res = self.testapp.get(calendar_url, params={'sortOn': 'end_time', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('B', 'b1', 'aa', 'AAA'))

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def testCalendarViews(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            calendar = MockCalendar(title=u"study")
            calendar.containerId = u'container_id'
            calendar.id = u'container_id'
            interface.alsoProvides(calendar, IContained)

            user = self._create_user(username)
            user.addContainedObject(calendar)

            calendar_ntiid = to_external_ntiid_oid(calendar)
            assert_that(calendar_ntiid, not_none())

        calendar_url = '/dataserver2/Objects/%s' % calendar_ntiid
        res = self.testapp.get(calendar_url, status=200).json_body
        self.require_link_href_with_rel(res, 'edit')

        with mock_dataserver.mock_db_trans(self.ds):
            for created, title, description, location, start_time, end_time in (
                                                                    (50, u"1a", u"1b", u"1c", datetime(2018, 10, 23), datetime(2018, 11, 23, 0, 0, 0)),
                                                                    (60, u"2a", u"2b", u"2c", datetime(2018, 10, 24), datetime(2018, 11, 19, 0, 0, 0)),
                                                                    (40, u"3a", u"3b", u"6c", datetime(2018, 10, 22), datetime(2018, 11, 24, 0, 0, 0)),
                                                                    (30, u"4a", u"6b", u"3c", datetime(2018, 10, 25), datetime(2018, 11, 26, 0, 0, 0)),
                                                                    (10, u"6a", u"4b", u"4c", datetime(2018, 10, 21), datetime(2018, 11, 25, 0, 0, 0)),
                                                                    (20, u"5a", u"5b", u"5c", datetime(2018, 10, 20), datetime(2018, 11, 20, 0, 0, 0))):
                event = CalendarEvent(title=title,
                                      description=description,
                                      location=location,
                                      icon=u'/home/nt',
                                      start_time=start_time,
                                      end_time=end_time)
                event.createdTime = created
                calendar.store_event(event)

        # Get
        res = self.testapp.get(calendar_url, status=200).json_body
        assert_that(res, has_entries({'title': 'study',
                                      'description': None,
                                      'MimeType': 'application/vnd.nextthought.calendar.calendar'}))
        self.require_link_href_with_rel(res, 'edit')
        self.require_link_href_with_rel(res, 'contents')

        # Update
        params = {
            "title": "okc",
            "description": "this is okc"
        }
        res = self.testapp.put_json(calendar_url, params=params, status=200).json_body
        assert_that(res, has_entries({'title': 'okc',
                                      'description': 'this is okc',
                                      'MimeType': 'application/vnd.nextthought.calendar.calendar'}))


        # calendar events
        calendar_url = calendar_url + '/@@contents'
        res = self.testapp.get(calendar_url, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6),
                                      'Total': is_(6)}))

        # sort
        for field, expected_result, ext_field in (
                    ('createdtime', (10, 20, 30, 40, 50, 60), "CreatedTime"),
                    ('lastModified', ("1a", "2a", "3a", "4a", "6a", "5a"), "title"),
                    ('title', ('1a', '2a', '3a', '4a', '5a', '6a'), None),
                    ('description', ('1b', '2b', '3b', '4b', '5b', '6b'), None),
                    ('location', ('1c', '2c', '3c', '4c', '5c', '6c'), None),
                    ('start_time', ("2018-10-20T00:00:00Z", "2018-10-21T00:00:00Z", "2018-10-22T00:00:00Z", "2018-10-23T00:00:00Z", "2018-10-24T00:00:00Z", "2018-10-25T00:00:00Z"), None),
                    ('end_time', ("2018-11-19T00:00:00Z", "2018-11-20T00:00:00Z", "2018-11-23T00:00:00Z", "2018-11-24T00:00:00Z", "2018-11-25T00:00:00Z", "2018-11-26T00:00:00Z"), None) ):
            for order, _expected in ( ('ascending', expected_result),
                                      ('descending', expected_result[::-1])):
                res = self.testapp.get(calendar_url, params={'sortOn': field, 'sortOrder': order}, status=200).json_body
                assert_that(res, has_entries({'Items': has_length(6), 'Total': 6}))
                assert_that([x[ext_field or field] for x in res['Items']], contains(*_expected))

        # bad sortOn
        res = self.testapp.get(calendar_url, params={'sortOn': "abc"}, status=422).json_body
        assert_that(res['message'], is_("Invalid value for 'sortOn'"))

        # bad sortOrder
        res = self.testapp.get(calendar_url, params={'sortOrder': "abc"}, status=422).json_body
        assert_that(res['message'], is_("Invalid value for 'sortOrder'"))

        # Test filter

        # 2018-10-20 ~ 2018-11-26, return all items
        res = self.testapp.get(calendar_url, params={'notBefore': '1539993600', 'notAfter': '1543190400'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6), 'FilteredTotalItemCount': is_(6)}))

        # 2018-10-20 ~
        res = self.testapp.get(calendar_url, params={'notBefore': '1539993600'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6), 'FilteredTotalItemCount': is_(6)}))

        # ~ 2018-11-26
        res = self.testapp.get(calendar_url, params={'notAfter': '1543190400'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6), 'FilteredTotalItemCount': is_(6)}))

        # 2018-11-26 ~
        res = self.testapp.get(calendar_url, params={'notBefore': '1543190400'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('4a'))

        # 2018-11-26 ~ 2018-11-26
        res = self.testapp.get(calendar_url, params={'notBefore': '1543190400', 'notAfter': '1543190400'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('4a'))

        # 2018-11-26 00:00:01 ~
        res = self.testapp.get(calendar_url, params={'notBefore': '1543190401'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(6), 'FilteredTotalItemCount': is_(0)}))

        # ~ 2018-10-20
        res = self.testapp.get(calendar_url, params={'notAfter': '1539993600'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('5a'))

        # 2018-10-20 ~ 2018-10-20
        res = self.testapp.get(calendar_url, params={'notAfter': '1539993600', 'notBefore': '1539993600'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('5a'))

        # ~ 2018-10-19 23:59:59
        res = self.testapp.get(calendar_url, params={'notAfter': '1539993599', 'sortOn': 'title', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(6), 'FilteredTotalItemCount': is_(0)}))

        # 2018-10-21 ~ 2018-10-22
        res = self.testapp.get(calendar_url, params={'notBefore': '1540080000', 'notAfter': '1540166400', 'sortOn': 'title', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('3a', '5a', '6a'))

        # 2018-12-01 ~ 2018-12-02
        res = self.testapp.get(calendar_url, params={'notBefore': '1543622400', 'notAfter': '1543708800'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(6), 'FilteredTotalItemCount': is_(0)}))

        # 2018-09-01 ~ 2018-09-03
        res = self.testapp.get(calendar_url, params={'notBefore': '1535760000', 'notAfter': '1535932800'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(6), 'FilteredTotalItemCount': is_(0)}))

        # notBefore can not be greater then notAfter
        res = self.testapp.get(calendar_url, params={'notBefore': '20', 'notAfter': '10'}, status=422).json_body
        assert_that(res['message'], is_("notBefore should be less than notAfter"))

        # mimeType
        res = self.testapp.get(calendar_url, params={'mimeType': 'application/vnd.nextthought.calendar.calendarevent'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6), 'FilteredTotalItemCount': is_(6)}))

        res = self.testapp.get(calendar_url, params={'mimeType': ''}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6)}))

        res = self.testapp.get(calendar_url, params={'mimeType': 'abc'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(6), 'FilteredTotalItemCount': is_(0)}))

        # Test end_time which may be None.
        with mock_dataserver.mock_db_trans(self.ds):
            event = CalendarEvent(title="Testing No End_Time", icon=u'/home/nt', end_time=None)
            calendar.store_event(event)
            assert_that(event.start_time, not_none())
            assert_that(event.end_time, is_(None))

        res = self.testapp.get(calendar_url, params={}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(7), 'Total': is_(7)}))

        # 2018-07-06 ~ 2018-07-06
        res = self.testapp.get(calendar_url, params={'notBefore': '1530835200', 'notAfter': '1530835200'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(7)}))

        # Calendar feed (consistent)
        generate_feed_url = '/dataserver2/users/sjohnson@nextthought.com/Calendars/@@GenerateFeedURL'
        res = self.testapp.get(generate_feed_url)
        feed_url = res.json_body
        assert_that(feed_url,
                    contains_string('/dataserver2/@@calendar_feed.ics?token='))
        res = self.testapp.get(generate_feed_url)
        assert_that(res.json_body,
                    is_(feed_url))
        self.testapp.get(feed_url)

        # Now test size constraints (google calendar only works with a
        # <256 char url)
        assert_that(len(feed_url), less_than_or_equal_to(256))
        longer_url = feed_url.replace('localhost', 'epiccharterschools.nextthought.com')
        assert_that(len(longer_url), less_than_or_equal_to(256))


class TestCalendarAttendanceViews(CalendarLayerTest):

    @staticmethod
    def _registration_time():
        registration_time = (datetime.utcnow().replace(microsecond=0))
        return datetime_to_string(registration_time)

    def _event_acl(self, principals_with_read):
        aces = [ace_allowing(ROLE_ADMIN, ACT_RECORD_EVENT_ATTENDANCE, type(self)),
                ace_allowing(ROLE_ADMIN, ACT_VIEW_EVENT_ATTENDANCE, type(self)),
                ace_allowing(ROLE_ADMIN, ACT_READ, type(self))]
        for prin in principals_with_read or ():
            aces.append(ace_allowing(prin, ACT_READ, type(self)))
        aces.append(ace_denying_all())
        acl = acl_from_aces(aces)
        return acl

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def test_attendence_csv_export(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._create_user(username)

            calendar = self._create_calendar(user)
            event = self._create_event(user, calendar,
                                       allowed_principals=('test_student1',
                                                           'test_student2'))
            event_ntiid = event.ntiid
            assert_that(event_ntiid, not_none())

        assert_that(event_ntiid, not_none())

        event_url = '/dataserver2/Objects/%s' % event_ntiid
        res = self.testapp.get(event_url).json_body
        self.require_link_href_with_rel(res, 'export-attendance')

        record_attendance_url = '%s/EventAttendance' % event_url

        record_attendance = partial(self.record_attendance, record_attendance_url)

        admin_env = self._make_extra_environ()

        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user('test_student1',
                              external_value={
                                  'realname': u'Uno Student',
                              })
            self._create_user('test_student2',
                              external_value={
                                  'realname': u'Dos Student',
                              })

        export_attendance_url = '%s/@@ExportAttendance' % record_attendance_url
        res = self.testapp.get(export_attendance_url)
        assert_that(res.body,
                    is_('Username,Real Name,Registration Time\r\n'))

        registration_time_1 = self._registration_time()
        record_attendance(admin_env, 'test_student1', registration_time_1)

        registration_time_2 = self._registration_time()
        record_attendance(admin_env, 'test_student2', registration_time_2)

        res = self.testapp.get(export_attendance_url)
        assert_that(res.body,
                    is_('Username,Real Name,Registration Time\r\n'
                        + ('test_student1,Uno Student,%s\r\n' % registration_time_1)
                        + ('test_student2,Dos Student,%s\r\n' % registration_time_2)))

        with mock_dataserver.mock_db_trans(self.ds):
            User.delete_user('test_student1')

        res = self.testapp.get(export_attendance_url)
        assert_that(res.body,
                    is_('Username,Real Name,Registration Time\r\n'
                        + ('test_student2,Dos Student,%s\r\n' % registration_time_2)))

        @interface.implementer(IProfileDisplayableSupplementalFields)
        class _TestSupplementalFields(object):

            def get_user_fields(self, _user):
                return {'field_1': 'value_1'}

            def get_field_display_values(self):
                return {'field_1': "Field One", 'field_2': "Field Two"}

            def get_ordered_fields(self):
                return ['field_1', 'field_2']

        with _provide_utility(_TestSupplementalFields(),
                              IProfileDisplayableSupplementalFields):

            res = self.testapp.get(export_attendance_url)
            assert_that(res.body,
                        is_('Username,Real Name,Registration Time,Field One,Field Two\r\n'
                            + ('test_student2,Dos Student,%s,value_1,\r\n' % registration_time_2)))

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def test_search(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._create_user(username,
                                     external_value={
                                         'realname': u'Ben Owner'
                                     })
            self._create_user('unsearchable',
                              external_value={
                                  'realname': u'Xao Ma',
                              })

            calendar = self._create_calendar(user)

            event = self._create_event(user, calendar)
            event_ntiid = event.ntiid
            assert_that(event_ntiid, not_none())

        event_url = '/dataserver2/Objects/%s' % event_ntiid
        res = self.testapp.get(event_url).json_body

        base_search_url = \
            self.require_link_href_with_rel(res, 'search-possible-attendees')

        res = self.testapp.get("%s/Owner" % base_search_url).json_body
        assert_that(res['Items'], has_length(1))
        assert_that(res['Items'][0],
                    has_entries(User=has_entries(Username=username)))
        self.forbid_link_with_rel(res['Items'][0], 'attendance')

        res = self.testapp.get("%s/Xao" % base_search_url).json_body
        assert_that(res['Items'], has_length(0))

        # Record attendance for searchable user (owner)
        record_attendance_url = '%s/EventAttendance' % event_url
        admin_env = self._make_extra_environ()
        self.record_attendance(record_attendance_url, admin_env, username)

        # Ensure attendance metadata is updated
        res = self.testapp.get("%s/Owner" % base_search_url).json_body
        assert_that(res['Items'], has_length(1))
        assert_that(res['Items'][0],
                    has_entries(User=has_entries(Username=username)))
        self.require_link_href_with_rel(res['Items'][0], 'attendance')

    def record_attendance(self, record_attendance_url, env, username_,
                          registration_time=None, **kwargs):
        kwargs['extra_environ'] = env
        data = {
            'Username': username_,
            'registrationTime': registration_time,
        }
        return self.testapp.post_json(record_attendance_url, data, **kwargs)

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def test_registration_time_decoration(self):
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._get_user(self.default_username)
            self._create_user('student_one',
                              external_value={
                                  'realname': u'Maybe Attendee',
                              })

            calendar = self._create_calendar(user)

            event = self._create_event(user, calendar,
                                       allowed_principals=('student_one',))
            event_ntiid = event.ntiid
            assert_that(event_ntiid, not_none())

        event_url = '/dataserver2/Objects/%s' % event_ntiid

        # Admin/Owner shouldn't have a registration time
        res = self.testapp.get(event_url).json_body
        assert_that(res, not_(has_item('RegistrationTime')))

        # Attendee shouldn't have a registration time yet
        attendee_env = self._make_extra_environ('student_one')
        res = self.testapp.get(event_url, extra_environ=attendee_env).json_body
        assert_that(res, not_(has_item('RegistrationTime')))

        # Record attendance for attendee
        record_attendance_url = '%s/EventAttendance' % event_url
        admin_env = self._make_extra_environ()
        registration_time = self._registration_time()
        self.record_attendance(record_attendance_url, admin_env, 'student_one',
                               registration_time=registration_time)

        # Admin/Owner shouldn't have a registration time
        res = self.testapp.get(event_url).json_body
        assert_that(res, not_(has_item('RegistrationTime')))

        # Attendee should now have a registration time
        attendee_env = self._make_extra_environ('student_one')
        res = self.testapp.get(event_url, extra_environ=attendee_env).json_body
        assert_that(res.get('RegistrationTime'), is_(registration_time))

    def _create_event(self, user, calendar, allowed_principals=None):
        event = CalendarEvent(title="Test Event")
        event.creator = user
        event.__acl__ = self._event_acl(allowed_principals)
        return calendar.store_event(event)

    def _create_calendar(self, user):
        calendar = MockCalendar(title=u"study")
        calendar.containerId = u'container_id'
        calendar.id = u'container_id'
        interface.alsoProvides(calendar, IContained)
        user.addContainedObject(calendar)
        return calendar


@contextmanager
def _provide_utility(util, provided):
    gsm = component.getGlobalSiteManager()
    gsm.registerUtility(util, provided)
    try:
        yield
    finally:
        gsm.unregisterUtility(util, provided)
