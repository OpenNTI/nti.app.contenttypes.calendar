#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from datetime import datetime

import fudge

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import contains_inanyorder

from zope import component
from zope import interface

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.contenttypes.calendar.entity.model import UserCalendarEvent
from nti.app.contenttypes.calendar.entity.model import CommunityCalendarEvent
from nti.app.contenttypes.calendar.entity.model import FriendsListCalendarEvent

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.utils import get_indexed_calendar_events

from nti.dataserver.tests import mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import Community
from nti.dataserver.users import DynamicFriendsList


class TestIndex(ApplicationLayerTest):

    @WithMockDSTrans
    def test_not_before_and_after(self):
        def _adjust_ts(ts):
            return datetime.fromtimestamp(ts)

        community = Community.create_community(self.ds, username=u'test001')
        calendar =ICalendar(community)
        event1 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(1000), end_time=_adjust_ts(1100)))
        event2 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(1000), end_time=_adjust_ts(1200)))
        event3 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(1000), end_time=_adjust_ts(3600)))
        event4 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(1199), end_time=_adjust_ts(3660)))
        event5 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(1199), end_time=None))

        event6 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(1200), end_time=_adjust_ts(2500)))
        event7 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(1600), end_time=_adjust_ts(3600)))
        event8 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(3600), end_time=_adjust_ts(3660)))
        event9 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(3600), end_time=_adjust_ts(4000)))
        event10 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(3600), end_time=None))

        event11 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(3660), end_time=_adjust_ts(4000)))
        event12 = calendar.store_event(CommunityCalendarEvent(title=u'one', start_time=_adjust_ts(3660), end_time=None))

        result = get_indexed_calendar_events()
        assert_that(result, has_length(0))

        # normalizing to mins.
        # if we change below params notBefore/notAfter to be timestamp
        # it may fail in the non-utc environment.

        # notBefore, notAfter
        notBefore, notAfter = _adjust_ts(1200), _adjust_ts(3600)
        result = get_indexed_calendar_events(notBefore=notBefore, notAfter=notAfter)
        assert_that(result, has_length(8))
        assert_that(result, contains_inanyorder(event2, event3, event4, event6, event7, event8, event9, event10))

        result = get_indexed_calendar_events(notBefore=notBefore)
        assert_that(result, has_length(10))
        assert_that(result, contains_inanyorder(event2, event3, event4, event6, event7, event8, event9, event10, event11, event12))

        result = get_indexed_calendar_events(notAfter=notAfter)
        assert_that(result, has_length(10))
        assert_that(result, contains_inanyorder(event1, event2, event3, event4, event5, event6, event7, event8, event9, event10))

        result = get_indexed_calendar_events(notBefore=_adjust_ts(3660))
        assert_that(result, has_length(5))
        assert_that(result, contains_inanyorder(event4, event8, event9, event11, event12))

        result = get_indexed_calendar_events(notBefore=_adjust_ts(960))
        assert_that(result, has_length(12))

        result = get_indexed_calendar_events(notAfter=_adjust_ts(3660))
        assert_that(result, has_length(12))

        result = get_indexed_calendar_events(notAfter=_adjust_ts(960))
        assert_that(result, has_length(3))
        assert_that(result, contains_inanyorder(event1,event2, event3))

    @WithMockDSTrans
    def test_mimetypes(self):
        # community
        community = Community.create_community(self.ds, username=u'community001')
        comm_event_one = ICalendar(community).store_event(CommunityCalendarEvent(title=u'comm_one',
                                                                                 start_time=datetime.utcfromtimestamp(1541635200), # 2018-11-08T00:00:00Z
                                                                                 end_time=datetime.utcfromtimestamp(1541721600))) # 2018-11-09T00:00:00Z

        # user
        user = self._create_user(u'user001')
        user_event_one = ICalendar(user).store_event(UserCalendarEvent(title=u'u_one'))
        user_event_two = ICalendar(user).store_event(UserCalendarEvent(title=u'u_two'))

        # group
        group =  user.addContainedObject(DynamicFriendsList(username=u'group001'))
        calendar = ICalendar(group)
        g_event_one = calendar.store_event(FriendsListCalendarEvent(title=u'g_one'))
        g_event_two = calendar.store_event(FriendsListCalendarEvent(title=u'g_two'))
        g_event_three = calendar.store_event(FriendsListCalendarEvent(title=u'g_three'))

        result = get_indexed_calendar_events()
        assert_that(result, has_length(0))

        result = get_indexed_calendar_events(mimeTypes='application/vnd.nextthought.calendar.communitycalendarevent')
        assert_that(result, contains_inanyorder(comm_event_one))

        result = get_indexed_calendar_events(mimeTypes='application/vnd.nextthought.calendar.usercalendarevent')
        assert_that(result, contains_inanyorder(user_event_one, user_event_two))

        result = get_indexed_calendar_events(mimeTypes='application/vnd.nextthought.calendar.friendslistcalendarevent')
        assert_that(result, contains_inanyorder(g_event_one, g_event_two, g_event_three))

        result = get_indexed_calendar_events(mimeTypes=['application/vnd.nextthought.calendar.usercalendarevent',
                                                        'application/vnd.nextthought.calendar.communitycalendarevent'])
        assert_that(result, contains_inanyorder(user_event_one, user_event_two, comm_event_one))

        result = get_indexed_calendar_events(mimeTypes=['application/vnd.nextthought.calendar.usercalendarevent', 'abc'])
        assert_that(result, contains_inanyorder(user_event_one, user_event_two))

        result = get_indexed_calendar_events(mimeTypes=['abc'])
        assert_that(result, has_length(0))
