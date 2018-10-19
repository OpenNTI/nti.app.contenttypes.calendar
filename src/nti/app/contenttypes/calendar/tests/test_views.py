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

            for title, description, location, start_time, end_time in ((u"1a", u"1b", u"1c", datetime(2018, 10, 23), datetime(2018, 11, 23)),
                                                                       (u"2a", u"2b", u"2c", datetime(2018, 10, 24), None),
                                                                       (u"3a", u"3b", u"6c", datetime(2018, 10, 22), datetime(2018, 11, 24)),
                                                                       (u"4a", u"6b", u"3c", None, datetime(2018, 11, 26)),
                                                                       (u"6a", u"4b", u"4c", datetime(2018, 10, 21), datetime(2018, 10, 25)),
                                                                       (u"5a", u"5b", u"5c", datetime(2018, 10, 20), datetime(2018, 10, 20))):
                event = CalendarEvent(title=title,
                                      description=description,
                                      location=location,
                                      icon=u'/home/nt',
                                      start_time=start_time,
                                      end_time=end_time)
                calendar.store_event(event)

        assert_that(calendar_ntiid, not_none())

        calendar_url = '/dataserver2/Objects/%s' % calendar_ntiid

        # Get
        res = self.testapp.get(calendar_url, status=200).json_body
        assert_that(res, has_entries({'title': 'study',
                                      'description': None,
                                      'MimeType': 'application/vnd.nextthought.calendar.calendar'}))

        # Update
        params = {
            "title": "okc",
            "description": "this is okc"
        }
        res = self.testapp.put_json(calendar_url, params=params, status=200).json_body
        assert_that(res, has_entries({'title': 'okc',
                                      'description': 'this is okc',
                                      'MimeType': 'application/vnd.nextthought.calendar.calendar'}))

        # Batch views
