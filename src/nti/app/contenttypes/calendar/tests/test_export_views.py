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


def _mock_calendars():
    return [MockCalendar(title=u"study"),
            MockCalendar(title=u"play")]


class TestBulkCalendarExportView(CalendarLayerTest):

    @WithSharedApplicationMockDS(users=True, testapp=True, default_authenticate=True)
    @with_patched_object("nti.app.contenttypes.calendar.export_views.BulkCalendarExportView", "_calendars", _mock_calendars())
    def test_bulk_export(self):
        username = u'testuser001@nextthought.com'
        with mock_dataserver.mock_db_trans(self.ds):
            calendar = MockCalendar(title=u"study")
            calendar.containerId = u'container_id'
            calendar.id = u'container_id'
            interface.alsoProvides(calendar, IContained)

            user = self._create_user(username)
            user.addContainedObject(calendar)

            view = BulkCalendarExportView(self.request)
            assert_that(view._generate_calendar_filename(calendar), is_(u'study.ics'))
            assert_that(view._generate_calendar_filename(calendar), is_(u'study_1.ics'))
            assert_that(view._generate_calendar_filename(calendar), is_(u'study_2.ics'))

            calendar.title = u''
            assert_that(view._generate_calendar_filename(calendar), is_(u'calendar.ics'))
            assert_that(view._generate_calendar_filename(calendar), is_(u'calendar_1.ics'))
            assert_that(view._generate_calendar_filename(calendar), is_(u'calendar_2.ics'))

        calendar_url = '/dataserver2/users/%s/Calendars/@@export' % username
        res = self.testapp.get(calendar_url, status=200)
        stream = BytesIO()
        stream.write(res.body)
        zfile = ZipFile(stream)
        assert_that([x.filename for x in zfile.filelist], contains_inanyorder('sjohnson@nextthought.com_calendars/',
                                                                              'sjohnson@nextthought.com_calendars/play.ics',
                                                                              'sjohnson@nextthought.com_calendars/study.ics'))
