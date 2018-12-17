#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

import fudge

from fudge.patcher import with_patched_object

from hamcrest import is_
from hamcrest import contains
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_entries
from hamcrest import has_length
from hamcrest import has_properties
from hamcrest import assert_that
from hamcrest import contains_inanyorder

from datetime import datetime

from icalendar import Calendar as iCalendar

from io import BytesIO

from zipfile import ZipFile

from zope import interface
from zope import component

from nti.app.contenttypes.calendar.tests import CalendarLayerTest

from nti.app.contenttypes.calendar.export_views import BulkCalendarExportView

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.contenttypes.calendar.model import Calendar
from nti.contenttypes.calendar.model import CalendarEvent

from nti.coremetadata.interfaces import IContained

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users.users import User

from nti.dataserver.authorization import ROLE_ADMIN

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces
from nti.dataserver.authorization_acl import ace_denying_all

from nti.dataserver.interfaces import ALL_PERMISSIONS

from nti.ntiids.oids import to_external_ntiid_oid

class MockCalendar(Calendar):

    def __acl__(self):
        aces = [ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, type(self)),
                ace_denying_all()]
        acl = acl_from_aces(aces)
        return acl


class TestCalendarExportView(CalendarLayerTest):

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def test_calendar_export(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            calendar = MockCalendar(title=u"study")
            calendar.containerId = u'container_id'
            calendar.id = u'container_id'
            interface.alsoProvides(calendar, IContained)

            user = self._create_user(username)
            user.addContainedObject(calendar)

            calendar_ntiid = to_external_ntiid_oid(calendar)

            event = CalendarEvent(title=u'Golf',
                                 description=u'golf training',
                                 location=u'Westwood golf court',
                                 start_time=datetime.utcfromtimestamp(1541721600), # 2018-11-09T00:00:00Z
                                 end_time=datetime.utcfromtimestamp(1541808000), # 2018-11-10T00:00:00Z
                                 icon=u'/abc/efg')
            calendar.store_event(event)
            event_ntiid = to_external_ntiid_oid(event)

        calendar_url = '/dataserver2/Objects/%s/@@export' % calendar_ntiid
        res = self.testapp.get(calendar_url, status=200)

        cal = iCalendar.from_ical(res.body)
        assert_that(cal['title'], is_('study'))
        assert_that(cal['description'], is_(''))
        assert_that(cal['X-NTIID'], is_(calendar_ntiid))
        assert_that(cal['X-NTI-MIMETYPE'], is_('application/vnd.nextthought.calendar.calendar'))
        assert_that(cal.subcomponents, has_length(1))

        eve = cal.subcomponents[0]
        assert_that(eve['X-NTIID'], is_(event_ntiid))
        assert_that(eve['X-NTI-MIMETYPE'], is_('application/vnd.nextthought.calendar.calendarevent'))
        assert_that(eve['summary'], is_('Golf'))
        assert_that(eve['description'], is_('golf training'))
        assert_that(eve['location'], is_('Westwood golf court'))
        assert_that(eve['dtstart'].to_ical(), is_('20181109T000000Z'))
        assert_that(eve['dtend'].to_ical(), is_('20181110T000000Z'))
        assert_that(eve['dtstamp'], not_none())
        assert_that(eve['created'], not_none())
        assert_that(eve['last-modified'], not_none())


class TestBulkCalendarExportView(CalendarLayerTest):

    def _add_calendar(self, user, title=u'study'):
        calendar = MockCalendar(title=title)
        calendar.containerId = u'container_id' + title
        calendar.id = u'container_id' + title
        interface.alsoProvides(calendar, IContained)
        user.addContainedObject(calendar)
        return calendar

    def _add_event(self, calendar, title=u'Golf'):
        event = CalendarEvent(title=title,
                             description=u'golf training',
                             location=u'Westwood golf court',
                             start_time=datetime.utcfromtimestamp(1541721600), # 2018-11-09T00:00:00Z
                             end_time=datetime.utcfromtimestamp(1541808000), # 2018-11-10T00:00:00Z
                             icon=u'/abc/efg')
        return calendar.store_event(event)

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    def test_bulk_export(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._create_user(username)

        calendar_url = '/dataserver2/users/%s/Calendars/@@export' % username
        res = self.testapp.get(calendar_url, status=200)

        cal = iCalendar.from_ical(res.body)
        assert_that(cal['title'], is_('My Calendars'))
        assert_that(cal.subcomponents, has_length(0))

        with mock_dataserver.mock_db_trans(self.ds):
            class _mock_ws(object):
                def __init__(self, user):
                    self.user = user

            view = BulkCalendarExportView(self.request)
            view._calendars = []

            res = iCalendar.from_ical(view._build_icalendar())
            assert_that(res['title'], 'My Calendars')
            assert_that(res.subcomponents, has_length(0))

            # add calendar 1
            calendar1 = self._add_calendar(user,title=u'study')
            event1 = self._add_event(calendar1, title=u'golf')
            view._calendars =[calendar1]

            res = iCalendar.from_ical(view._build_icalendar())
            assert_that(res['title'], 'My Calendars')
            assert_that(res.subcomponents, has_length(1))
            assert_that(res.subcomponents[0]['summary'], is_(u'golf'))

            # add calendar 2
            calendar2 = self._add_calendar(user, title=u'work')
            event2 = self._add_event(calendar2, title=u'tennis')
            event3 = self._add_event(calendar2, title=u'tennis3')
            view._calendars =[calendar2]

            res = iCalendar.from_ical(view._build_icalendar())
            assert_that(res['title'], 'My Calendars')
            assert_that(res.subcomponents, has_length(2))
            assert_that(res.subcomponents[0]['summary'], is_(u'tennis'))
            assert_that(res.subcomponents[1]['summary'], is_(u'tennis3'))

            # add calendar 1 & 2
            view._calendars =[calendar1, calendar2]

            res = iCalendar.from_ical(view._build_icalendar())
            assert_that(res['title'], 'My Calendars')
            assert_that(res.subcomponents, has_length(3))
            assert_that(res.subcomponents[0]['summary'], is_(u'golf'))
            assert_that(res.subcomponents[1]['summary'], is_(u'tennis'))
            assert_that(res.subcomponents[2]['summary'], is_(u'tennis3'))

        # post
        calendar_url = '/dataserver2/users/%s/Calendars/@@export' % username
        res = self.testapp.post(calendar_url, status=200)

        cal = iCalendar.from_ical(res.body)
        assert_that(cal['title'], is_('My Calendars'))
        assert_that(cal.subcomponents, has_length(0))

        res = self.testapp.post_json(calendar_url, params={'context_ntiids': False}, status=422).json_body
        assert_that(res['message'], is_('context_ntiids should be an array of ntiids or empty.'))

        res = self.testapp.post_json(calendar_url, params={'context_ntiids': 'abc'}, status=422).json_body
        assert_that(res['message'], is_('context_ntiids should be an array of ntiids or empty.'))

        res = self.testapp.post_json(calendar_url, params={'excluded_context_ntiids': False}, status=422).json_body
        assert_that(res['message'], is_('excluded_context_ntiids should be an array of ntiids or empty.'))

        self.testapp.post_json(calendar_url, params={'context_ntiids': ['a'], 'excluded_context_ntiids': []}, status=200)
