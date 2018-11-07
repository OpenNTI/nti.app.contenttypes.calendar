#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_
from hamcrest import is_in
from hamcrest import is_not
from hamcrest import raises
from hamcrest import calling
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import same_instance

from zope.annotation.interfaces import IAnnotations

from zope.container.interfaces import InvalidItemType

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendar

from nti.app.contenttypes.calendar.entity.model import UserCalendarEvent

from nti.contenttypes.calendar.model import CalendarEvent

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans


class TestAdapters(ApplicationLayerTest):

    @WithMockDSTrans
    def test_calendar(self):
        user = self._create_user(u'test001')

        connection = mock_dataserver.current_transaction
        connection.add(user)
        calendar = IUserCalendar(user, None)
        assert_that(calendar, is_not(none()))
        assert_that(calendar.__parent__, same_instance(user))

        assert_that(calendar, validly_provides(IUserCalendar))
        assert_that(calendar, verifiably_provides(IUserCalendar))

        event = UserCalendarEvent(title=u'gogo')
        calendar.store_event(event)

        assert_that(calendar, has_length(1))
        assert_that(event.id, is_in(calendar))
        assert_that(list(calendar), has_length(1))

        assert_that(calendar.retrieve_event(event.id), same_instance(event))
        assert_that(event.__parent__, same_instance(calendar))

        calendar.remove_event(event)
        assert_that(calendar, has_length(0))
        assert_that(event.__parent__, is_(None))

        annotations = IAnnotations(user)
        assert_that(annotations['UserCalendar'], same_instance(calendar))

        # bad calendar event type
        event = CalendarEvent(title=u'abc')
        assert_that(calling(calendar.store_event).with_args(event), raises(InvalidItemType))
