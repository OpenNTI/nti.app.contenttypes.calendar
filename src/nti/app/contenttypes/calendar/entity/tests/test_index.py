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
        community = Community.create_community(self.ds, username=u'test001')
        calendar =ICalendar(community)
        event = calendar.store_event(CommunityCalendarEvent(title=u'one',
                                                            start_time=datetime.utcfromtimestamp(1541635200), # 2018-11-08T00:00:00Z
                                                            end_time=datetime.utcfromtimestamp(1541721600))) # 2018-11-09T00:00:00Z

        result = get_indexed_calendar_events()
        assert_that(result, has_length(0))

        # normalizing to mins.
        # if we change below params notBefore/notAfter to be timestamp
        # it may fail in the non-utc environment.
        result = get_indexed_calendar_events(notBefore=datetime.utcfromtimestamp(1541721600))
        assert_that(result, contains_inanyorder(event))

        result = get_indexed_calendar_events(notBefore=datetime.utcfromtimestamp(1541721659))
        assert_that(result, contains_inanyorder(event))

        # get_indexed_calendar_events(notBefore=1541721660) return 1 in non-utc.
        result = get_indexed_calendar_events(notBefore=datetime.utcfromtimestamp(1541721660))
        assert_that(result, has_length(0))

        result = get_indexed_calendar_events(notAfter=datetime.utcfromtimestamp(1541635200))
        assert_that(result, contains_inanyorder(event))

        result = get_indexed_calendar_events(notAfter=datetime.utcfromtimestamp(1541635199))
        assert_that(result, has_length(0))

        result = get_indexed_calendar_events(notBefore=datetime.utcfromtimestamp(1541635200), notAfter=datetime.utcfromtimestamp(1541721659))
        assert_that(result, contains_inanyorder(event))

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
