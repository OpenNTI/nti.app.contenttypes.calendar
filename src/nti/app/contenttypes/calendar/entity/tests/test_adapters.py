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
from hamcrest import instance_of
from hamcrest import same_instance

from zope import component

from zope.annotation.interfaces import IAnnotations

from zope.container.interfaces import InvalidItemType

from zope.traversing.interfaces import IPathAdapter

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendar
from nti.app.contenttypes.calendar.entity.interfaces import ICommunityCalendar
from nti.app.contenttypes.calendar.entity.interfaces import IFriendsListCalendar

from nti.app.contenttypes.calendar.entity.model import UserCalendar
from nti.app.contenttypes.calendar.entity.model import UserCalendarEvent
from nti.app.contenttypes.calendar.entity.model import CommunityCalendar
from nti.app.contenttypes.calendar.entity.model import CommunityCalendarEvent
from nti.app.contenttypes.calendar.entity.model import FriendsListCalendar
from nti.app.contenttypes.calendar.entity.model import FriendsListCalendarEvent

from nti.contenttypes.calendar.model import CalendarEvent

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import Community
from nti.dataserver.users import FriendsList
from nti.dataserver.users import DynamicFriendsList


class TestAdapters(ApplicationLayerTest):

    @WithMockDSTrans
    def test_user_calendar(self):
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
        assert_that(annotations['Calendar'], same_instance(calendar))

        # bad calendar event type
        event = CalendarEvent(title=u'abc')
        assert_that(calling(calendar.store_event).with_args(event), raises(InvalidItemType))

    @WithMockDSTrans
    def test_community_calendar(self):
        community = Community.create_community(self.ds, username=u'test001')

        connection = mock_dataserver.current_transaction
        connection.add(community)
        calendar = ICommunityCalendar(community, None)
        assert_that(calendar, is_not(none()))
        assert_that(calendar.__parent__, same_instance(community))

        assert_that(calendar, validly_provides(ICommunityCalendar))
        assert_that(calendar, verifiably_provides(ICommunityCalendar))

        event = CommunityCalendarEvent(title=u'gogo')
        calendar.store_event(event)

        assert_that(calendar, has_length(1))
        assert_that(event.id, is_in(calendar))
        assert_that(list(calendar), has_length(1))

        assert_that(calendar.retrieve_event(event.id), same_instance(event))
        assert_that(event.__parent__, same_instance(calendar))

        calendar.remove_event(event)
        assert_that(calendar, has_length(0))
        assert_that(event.__parent__, is_(None))

        annotations = IAnnotations(community)
        assert_that(annotations['Calendar'], same_instance(calendar))

        # bad calendar event type
        event = CalendarEvent(title=u'abc')
        assert_that(calling(calendar.store_event).with_args(event), raises(InvalidItemType))

    @WithMockDSTrans
    def test_friendslist_calendar(self):
        obj = DynamicFriendsList(username=u'test001')
        connection = mock_dataserver.current_transaction
        connection.add(obj)
        calendar = IFriendsListCalendar(obj, None)
        assert_that(calendar, is_not(none()))
        assert_that(calendar.__parent__, same_instance(obj))

        assert_that(calendar, validly_provides(IFriendsListCalendar))
        assert_that(calendar, verifiably_provides(IFriendsListCalendar))

        event = FriendsListCalendarEvent(title=u'gogo')
        calendar.store_event(event)

        assert_that(calendar, has_length(1))
        assert_that(event.id, is_in(calendar))
        assert_that(list(calendar), has_length(1))

        assert_that(calendar.retrieve_event(event.id), same_instance(event))
        assert_that(event.__parent__, same_instance(calendar))

        calendar.remove_event(event)
        assert_that(calendar, has_length(0))
        assert_that(event.__parent__, is_(None))

        annotations = IAnnotations(obj)
        assert_that(annotations['Calendar'], same_instance(calendar))

        # bad calendar event type
        event = CalendarEvent(title=u'abc')
        assert_that(calling(calendar.store_event).with_args(event), raises(InvalidItemType))

        # only support dynamic sharing friends lists
        obj = FriendsList(username=u'test002')
        mock_dataserver.current_transaction.add(obj)
        assert_that(IFriendsListCalendar(obj, None), is_(None))

    @WithMockDSTrans
    def test_user_calendar_path_adapter(self):
        user = self._create_user(u'test001')
        adapter = component.queryMultiAdapter((user, self.request), IPathAdapter, name='Calendar')
        assert_that(adapter, instance_of(UserCalendar))
        assert_that(adapter.__name__, is_('Calendar'))
        assert_that(adapter.__parent__, same_instance(user))

    @WithMockDSTrans
    def test_community_calendar_path_adapter(self):
        community = Community.create_community(self.ds, username=u'test001')
        adapter = component.queryMultiAdapter((community, self.request), IPathAdapter, name='Calendar')
        assert_that(adapter, instance_of(CommunityCalendar))
        assert_that(adapter.__name__, is_('Calendar'))
        assert_that(adapter.__parent__, same_instance(community))

    @WithMockDSTrans
    def test_friendslist_calendar_path_adapter(self):
        friendsList = DynamicFriendsList(username=u'test001')
        mock_dataserver.current_transaction.add(friendsList)
        adapter = component.queryMultiAdapter((friendsList, self.request), IPathAdapter, name='Calendar')
        assert_that(adapter, instance_of(FriendsListCalendar))
        assert_that(adapter.__name__, is_('Calendar'))
        assert_that(adapter.__parent__, same_instance(friendsList))

        obj = FriendsList(username=u'test002')
        mock_dataserver.current_transaction.add(obj)
        assert_that(component.queryMultiAdapter((obj, self.request), IPathAdapter, name='Calendar'), is_(None))
