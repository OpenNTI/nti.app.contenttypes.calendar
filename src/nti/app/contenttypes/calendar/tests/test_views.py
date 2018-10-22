#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import contains
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_entries
from hamcrest import has_length
from hamcrest import has_properties
from hamcrest import assert_that

from datetime import datetime

from zope import interface
from zope import component

from nti.app.contenttypes.calendar.tests import CalendarLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.contenttypes.calendar.model import Calendar
from nti.contenttypes.calendar.model import CalendarEvent

from nti.coremetadata.interfaces import IContained

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.users import User

from nti.ntiids.oids import to_external_ntiid_oid


class TestCalendarEventViews(CalendarLayerTest):

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def test_calendar_event_crud(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            calendar = Calendar(title=u"study")
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
        event_ntiid = res['NTIID']
        event_oid = res['OID']
        event_url = '/dataserver2/Objects/%s' % event_oid

        with mock_dataserver.mock_db_trans(self.ds):
            assert_that(calendar, has_length(1))
            event = calendar.retrieve_event(event_ntiid)
            assert_that(event, has_properties({'title': 'go to school',
                                               'description': 'let us go',
                                               'icon': '/home/go',
                                               'location': 'oklahoma',
                                               'start_time': not_none(),
                                               'end_time': not_none()}))

        # Get
        res = self.testapp.get(event_url, status=200).json_body
        assert_that(res, has_entries({"MimeType": "application/vnd.nextthought.calendar.calendarevent",
                                      "NTIID": event_ntiid}))
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
    def testCalendarViews(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            calendar = Calendar(title=u"study")
            calendar.containerId = u'container_id'
            calendar.id = u'container_id'
            interface.alsoProvides(calendar, IContained)

            user = self._create_user(username)
            user.addContainedObject(calendar)

            calendar_ntiid = to_external_ntiid_oid(calendar)
            assert_that(calendar_ntiid, not_none())

        calendar_url = '/dataserver2/Objects/%s' % calendar_ntiid
        res = self.testapp.get(calendar_url, params={'raw': True}, status=200).json_body
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
        res = self.testapp.get(calendar_url, params={'raw': True}, status=200).json_body
        assert_that(res, has_entries({'title': 'study',
                                      'description': None,
                                      'MimeType': 'application/vnd.nextthought.calendar.calendar'}))
        self.require_link_href_with_rel(res, 'edit')

        res = self.testapp.get(calendar_url, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6),
                                      'Total': is_(6)}))

        # Update
        params = {
            "title": "okc",
            "description": "this is okc"
        }
        res = self.testapp.put_json(calendar_url, params=params, status=200).json_body
        assert_that(res, has_entries({'title': 'okc',
                                      'description': 'this is okc',
                                      'MimeType': 'application/vnd.nextthought.calendar.calendar'}))

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
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6)}))

        # 2018-10-20 ~
        res = self.testapp.get(calendar_url, params={'notBefore': '1539993600'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6)}))

        # ~ 2018-11-26
        res = self.testapp.get(calendar_url, params={'notAfter': '1543190400'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6)}))

        # 2018-11-26 ~
        res = self.testapp.get(calendar_url, params={'notBefore': '1543190400'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('4a'))

        # 2018-11-26 ~ 2018-11-26
        res = self.testapp.get(calendar_url, params={'notBefore': '1543190400', 'notAfter': '1543190400'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('4a'))

        # 2018-11-26 00:00:01 ~
        res = self.testapp.get(calendar_url, params={'notBefore': '1543190401'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(0)}))

        # ~ 2018-10-20
        res = self.testapp.get(calendar_url, params={'notAfter': '1539993600'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('5a'))

        # 2018-10-20 ~ 2018-10-20
        res = self.testapp.get(calendar_url, params={'notAfter': '1539993600', 'notBefore': '1539993600'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('5a'))

        # ~ 2018-10-19 23:59:59
        res = self.testapp.get(calendar_url, params={'notAfter': '1539993599', 'sortOn': 'title', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(0)}))

        # 2018-10-21 ~ 2018-10-22
        res = self.testapp.get(calendar_url, params={'notBefore': '1540080000', 'notAfter': '1540166400', 'sortOn': 'title', 'sortOrder': 'ascending'}, status=200).json_body
        assert_that([x['title'] for x in res['Items']], contains('3a', '5a', '6a'))

        # 2018-12-01 ~ 2018-12-02
        res = self.testapp.get(calendar_url, params={'notBefore': '1543622400', 'notAfter': '1543708800'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(0)}))

        # 2018-09-01 ~ 2018-09-03
        res = self.testapp.get(calendar_url, params={'notBefore': '1535760000', 'notAfter': '1535932800'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(0)}))

        # notBefore can not be greater then notAfter
        res = self.testapp.get(calendar_url, params={'notBefore': '20', 'notAfter': '10'}, status=422).json_body
        assert_that(res['message'], is_("notBefore should be less than notAfter"))

        # mimeType
        res = self.testapp.get(calendar_url, params={'mimeType': 'application/vnd.nextthought.calendar.calendarevent'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6)}))

        res = self.testapp.get(calendar_url, params={'mimeType': ''}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(6), 'Total': is_(6)}))

        res = self.testapp.get(calendar_url, params={'mimeType': 'abc'}, status=200).json_body
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(0)}))

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
        assert_that(res, has_entries({'Items': has_length(0), 'Total': is_(0)}))
