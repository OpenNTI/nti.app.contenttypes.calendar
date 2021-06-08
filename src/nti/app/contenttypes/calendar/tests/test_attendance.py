#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import fudge

from hamcrest import assert_that
from hamcrest import contains_inanyorder
from hamcrest import has_length
from hamcrest import has_property

from pyramid.request import Request

from zope import interface

from nti.app.contenttypes.calendar.attendance import DefaultCalendarEventAttendanceLinkSource

from nti.app.contenttypes.calendar.tests import CalendarLayerTest

from nti.app.products.courseware.calendar.interfaces import ICourseCalendarEvent

from nti.contenttypes.calendar.interfaces import ICalendarDynamicEvent

from nti.contenttypes.calendar.model import CalendarEvent


class ITestCalendarDynamicEvent(ICourseCalendarEvent, ICalendarDynamicEvent):
    pass


@interface.implementer(ITestCalendarDynamicEvent)
class TestCalendarDynamicEvent(CalendarEvent):
    pass


class TestCalendarEventAttendanceLinkSource(CalendarLayerTest):

    @fudge.patch('nti.app.contenttypes.calendar.attendance.app_has_permission')
    def test_events(self, has_permission):
        has_permission.is_callable().returns(True)

        request = Request.blank('/')
        event = CalendarEvent(title=u'abc')

        link_source = DefaultCalendarEventAttendanceLinkSource(event, request)

        assert_that(link_source.links(), has_length(3))
        assert_that(link_source.links(), contains_inanyorder(
            has_property('rel', 'record-attendance'),
            has_property('rel', 'search-possible-attendees'),
            has_property('rel', 'list-attendance'),
        ))

    @fudge.patch('nti.app.contenttypes.calendar.attendance.app_has_permission')
    def test_dynamic_events(self, has_permission):
        has_permission.is_callable().returns(True)

        request = Request.blank('/')
        event = TestCalendarDynamicEvent(title=u'abc')

        link_source = DefaultCalendarEventAttendanceLinkSource(event, request)

        assert_that(link_source.links(), has_length(0))
