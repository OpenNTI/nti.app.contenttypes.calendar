#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from unittest import TestCase

import fudge

from hamcrest import assert_that
from hamcrest import contains_inanyorder
from hamcrest import has_entries
from hamcrest import has_key
from hamcrest import has_length
from hamcrest import has_property
from hamcrest import is_
from hamcrest import none
from hamcrest import not_

from pyramid.request import Request

from zope import interface

from nti.app.contenttypes.calendar.attendance import DefaultCalendarEventAttendanceLinkSource
from nti.app.contenttypes.calendar.attendance import EventUserSearchHit
from nti.app.contenttypes.calendar.interfaces import IEventUserSearchHit

from nti.app.contenttypes.calendar.tests import SharedConfiguringTestLayer

from nti.app.products.courseware.calendar.interfaces import ICourseCalendarEvent

from nti.app.products.courseware.interfaces import ACT_RECORD_EVENT_ATTENDANCE
from nti.app.products.courseware.interfaces import ACT_VIEW_EVENT_ATTENDANCE

from nti.contenttypes.calendar.interfaces import ICalendarDynamicEvent

from nti.contenttypes.calendar.model import CalendarEvent

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import User

from nti.externalization import internalization

from nti.externalization.externalization import toExternalObject

from nti.testing.matchers import verifiably_provides


class ITestCalendarDynamicEvent(ICourseCalendarEvent, ICalendarDynamicEvent):
    pass


@interface.implementer(ITestCalendarDynamicEvent)
class TestCalendarDynamicEvent(CalendarEvent):
    pass


def _make_has_permission(granted):

    granted = tuple(granted)

    def has_permission(perm, *_args):
        if perm in tuple(granted):
            return True
        return False

    return has_permission


class TestCalendarEventAttendanceLinkSource(TestCase):

    layer = SharedConfiguringTestLayer

    @staticmethod
    def _link_source(has_permission, granted):
        permission_check = _make_has_permission(granted)
        has_permission.is_callable().calls(permission_check)

        request = Request.blank('/')
        event = CalendarEvent(title=u'abc')

        link_source = DefaultCalendarEventAttendanceLinkSource(event, request)

        return link_source

    @fudge.patch('nti.app.contenttypes.calendar.attendance.app_has_permission')
    def test_all_perms(self, has_permission):
        granted = (ACT_RECORD_EVENT_ATTENDANCE, ACT_VIEW_EVENT_ATTENDANCE)
        link_source = self._link_source(has_permission, granted)

        assert_that(link_source.links(), contains_inanyorder(
            has_property('rel', 'record-attendance'),
            has_property('rel', 'search-possible-attendees'),
            has_property('rel', 'list-attendance'),
            has_property('rel', 'export-attendance'),
        ))

    @fudge.patch('nti.app.contenttypes.calendar.attendance.app_has_permission')
    def test_list_only(self, has_permission):
        granted = (ACT_VIEW_EVENT_ATTENDANCE,)
        link_source = self._link_source(has_permission, granted)

        assert_that(link_source.links(), contains_inanyorder(
            has_property('rel', 'list-attendance'),
            has_property('rel', 'export-attendance'),
        ))

    @fudge.patch('nti.app.contenttypes.calendar.attendance.app_has_permission')
    def test_record_only(self, has_permission):
        granted = [ACT_RECORD_EVENT_ATTENDANCE]
        link_source = self._link_source(has_permission, granted)

        assert_that(link_source.links(), contains_inanyorder(
            has_property('rel', 'record-attendance'),
            has_property('rel', 'search-possible-attendees'),
        ))

    @fudge.patch('nti.app.contenttypes.calendar.attendance.app_has_permission')
    def test_no_perms(self, has_permission):
        link_source = self._link_source(has_permission, ())

        assert_that(link_source.links(), has_length(0))

    @fudge.patch('nti.app.contenttypes.calendar.attendance.ICalendarEventAttendanceContainer')
    def test_no_container(self, container_adapter):
        container_adapter.is_callable().returns(None)

        request = Request.blank('/')
        event = CalendarEvent(title=u'abc')

        link_source = DefaultCalendarEventAttendanceLinkSource(event, request)

        assert_that(link_source.links(), has_length(0))

    @fudge.patch('nti.app.contenttypes.calendar.attendance.app_has_permission')
    def test_dynamic_events(self, has_permission):
        has_permission.is_callable().returns(True)

        request = Request.blank('/')
        event = TestCalendarDynamicEvent(title=u'abc')

        link_source = DefaultCalendarEventAttendanceLinkSource(event, request)

        assert_that(link_source.links(), has_length(0))


class TestEventUserSearchHit(TestCase):

    layer = SharedConfiguringTestLayer

    @WithMockDSTrans
    def test_provides(self):
        event = CalendarEvent(title=u'abc')
        user = User.create_user(username='test_user')

        search_hit = EventUserSearchHit(Event=event, User=user)

        assert_that(search_hit, verifiably_provides(IEventUserSearchHit))

    @WithMockDSTrans
    def test_externalize(self):
        event = CalendarEvent(title=u'abc')
        user = User.create_user(username='test_user')

        obj = EventUserSearchHit(Event=event, User=user)

        external = toExternalObject(obj)
        assert_that(external, has_entries({'User': has_entries(Username='test_user'),
                                           'MimeType': 'application/vnd.nextthought.calendar.eventusersearchhit'}))
        assert_that(external, not_(has_key('Event')))

        factory = internalization.find_factory_for(external)
        assert_that(factory, is_(none()))
