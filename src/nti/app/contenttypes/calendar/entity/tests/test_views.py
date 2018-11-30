#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import not_none
from hamcrest import has_entries
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import contains_inanyorder

from nti.app.contenttypes.calendar.tests import CalendarLayerTest

from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendar
from nti.app.contenttypes.calendar.entity.interfaces import ICommunityCalendar
from nti.app.contenttypes.calendar.entity.interfaces import IFriendsListCalendar

from nti.app.contenttypes.calendar.entity.model import UserCalendarEvent
from nti.app.contenttypes.calendar.entity.model import CommunityCalendarEvent
from nti.app.contenttypes.calendar.entity.model import FriendsListCalendarEvent

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users import User
from nti.dataserver.users import Community


class TestUserCalendarViews(CalendarLayerTest):

    @WithSharedApplicationMockDS(testapp=True, users=(u'test001', u'test002', u'admin001@nextthought.com'))
    def test_user_calendar(self):
        # Only owner could have all permissions.
        community_name = u'test.community.com'
        with mock_dataserver.mock_db_trans(self.ds):
            community = Community.create_community(self.ds, username=community_name)
            for username in (u'test001', u'test002', u'admin001@nextthought.com'):
                user = User.get_user('test001')
                user.record_dynamic_membership(community)

        admin_env = self._make_extra_environ(username='admin001@nextthought.com')
        owner_env = self._make_extra_environ(username='test001')
        other_env = self._make_extra_environ(username='test002')
        anonyous_env = self._make_extra_environ(username=None)

        # Read Calendar
        url = '/dataserver2/users/%s/Calendar' % u'test001'
        self.testapp.get(url, status=401, extra_environ=anonyous_env)
        self.testapp.get(url, status=403, extra_environ=other_env)
        self.testapp.get(url, status=403, extra_environ=admin_env)
        result = self.testapp.get(url, status=200, extra_environ=owner_env).json_body
        assert_that(result, has_entries({'MimeType': 'application/vnd.nextthought.calendar.usercalendar'}))

        # Create Event
        params = {
            "title": "go to school",
            "MimeType": "application/vnd.nextthought.calendar.usercalendarevent"
        }
        self.testapp.post_json(url, params=params, status=401, extra_environ=anonyous_env)
        self.testapp.post_json(url, params=params, status=403, extra_environ=other_env)
        self.testapp.post_json(url, params=params, status=403, extra_environ=admin_env)
        res = self.testapp.post_json(url, params=params, status=201, extra_environ=owner_env).json_body
        assert_that(res, has_entries({'title': 'go to school'}))
        EVENT_ID = res['ID']
        event_url = '%s/%s' % (url, EVENT_ID)

        # Read event.
        self.testapp.get(event_url, status=401, extra_environ=anonyous_env)
        self.testapp.get(event_url, status=403, extra_environ=other_env)
        self.testapp.get(event_url, status=403, extra_environ=admin_env)
        res = self.testapp.get(event_url, status=200, extra_environ=owner_env).json_body
        assert_that(res, has_entries({'MimeType': 'application/vnd.nextthought.calendar.usercalendarevent'}))

        # Update event.
        self.testapp.put_json(event_url, params=params, status=401, extra_environ=anonyous_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=other_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=admin_env)
        self.testapp.put_json(event_url, params=params, status=200, extra_environ=owner_env)

        # Delete Event.
        self.testapp.delete(event_url, status=401, extra_environ=anonyous_env)
        self.testapp.delete(event_url, status=403, extra_environ=other_env)
        self.testapp.delete(event_url, status=403, extra_environ=admin_env)
        self.testapp.delete(event_url, status=204, extra_environ=owner_env)


class TestCommunityCalendarViews(CalendarLayerTest):

    @WithSharedApplicationMockDS(testapp=True, users=(u'test001', u'test002', u'admin001@nextthought.com'))
    def test_community_calendar(self):
        # admin has all permissions
        # Community member has read permission.
        community_name = u'test.community.com'
        with mock_dataserver.mock_db_trans(self.ds):
            community = Community.create_community(self.ds, username=community_name)
            assert_that(ICommunityCalendar(community), not_none())

            user1 = User.get_user('test001')
            user1.record_dynamic_membership(community)

        admin_env = self._make_extra_environ(username='admin001@nextthought.com')
        member_env = self._make_extra_environ(username='test001')
        other_env = self._make_extra_environ(username='test002')
        anonyous_env = self._make_extra_environ(username=None)

        # Read Calendar.
        url = '/dataserver2/users/%s/Calendar' % community_name
        self.testapp.get(url, status=401, extra_environ=anonyous_env)
        self.testapp.get(url, status=403, extra_environ=other_env)
        self.testapp.get(url, status=200, extra_environ=member_env)
        result = self.testapp.get(url, status=200, extra_environ=admin_env).json_body
        assert_that(result, has_entries({'MimeType': 'application/vnd.nextthought.calendar.communitycalendar'}))

        # Create event.
        params = {
            "title": "go to school",
            "MimeType": "application/vnd.nextthought.calendar.communitycalendarevent"
        }
        self.testapp.post_json(url, params=params, status=401, extra_environ=anonyous_env)
        self.testapp.post_json(url, params=params, status=403, extra_environ=other_env)
        self.testapp.post_json(url, params=params, status=403, extra_environ=member_env)
        res = self.testapp.post_json(url, params=params, status=201, extra_environ=admin_env).json_body
        assert_that(res, has_entries({'title': 'go to school'}))
        EVENT_ID = res['ID']

        # Read event.
        event_url = '/dataserver2/users/%s/Calendar/%s' % (community_name, EVENT_ID)
        self.testapp.get(event_url, status=401, extra_environ=anonyous_env)
        self.testapp.get(event_url, status=403, extra_environ=other_env)
        self.testapp.get(event_url, status=200, extra_environ=member_env)
        res = self.testapp.get(event_url, status=200, extra_environ=admin_env).json_body
        assert_that(res, has_entries({'MimeType': 'application/vnd.nextthought.calendar.communitycalendarevent'}))

        # Update event.
        self.testapp.put_json(event_url, params=params, status=401, extra_environ=anonyous_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=other_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=member_env)
        self.testapp.put_json(event_url, params=params, status=200, extra_environ=admin_env)

        # Delete Event.
        self.testapp.delete(event_url, status=401, extra_environ=anonyous_env)
        self.testapp.delete(event_url, status=403, extra_environ=other_env)
        self.testapp.delete(event_url, status=403, extra_environ=member_env)
        self.testapp.delete(event_url, status=204, extra_environ=admin_env)


class TestFriendsListCalendarViews(CalendarLayerTest):

    def _create_group(self, username):
        params  = {
            "MimeType":"application/vnd.nextthought.dynamicfriendslist",
            "Username":"ohyeah-%s_d2a97129-6cc8-4f8a-b883-edcd78ade177" % username,
            "alias":"ohyeah",
            "friends":[],
            "IsDynamicSharing":True
        }
        url = '/dataserver2/users/%s/Groups' % username
        result = self.testapp.post_json(url, params=params, status=201, extra_environ=self._make_extra_environ(username=username)).json_body
        return result

    @WithSharedApplicationMockDS(testapp=True, users=(u'test001', u'test002', u'test003', u'test004', u'admin001@nextthought.com'))
    def test_group_calendar(self):
        # owner have all permissions on calendar, have read permission on all events.
        # friends have all permissions on events created by self, and have read permission on all events.
        res = self._create_group('test001')
        group_name = res['realname']
        url = res['href'] + '/Calendar'

        with mock_dataserver.mock_db_trans(self.ds):
            user = User.get_user('test001')
            friends = user.friendsLists[group_name]
            friends.addFriend(User.get_user('test002'))
            friends.addFriend(User.get_user('test003'))

        admin_env = self._make_extra_environ(username='admin001@nextthought.com')
        owner_env = self._make_extra_environ(username='test001')
        friend_env = self._make_extra_environ(username='test002')
        other_env = self._make_extra_environ(username='test004')
        anonyous_env = self._make_extra_environ(username=None)

        another_friend_env = self._make_extra_environ(username='test003')

        # GET
        self.testapp.get(url, status=401, extra_environ=anonyous_env)
        self.testapp.get(url, status=403, extra_environ=other_env)
        self.testapp.get(url, status=403, extra_environ=admin_env)
        self.testapp.get(url, status=200, extra_environ=friend_env)
        result = self.testapp.get(url, status=200, extra_environ=owner_env).json_body
        assert_that(result, has_entries({'MimeType': 'application/vnd.nextthought.calendar.friendslistcalendar'}))

        # Owner created event
        params = {
            "title": "go to school",
            "MimeType": "application/vnd.nextthought.calendar.friendslistcalendarevent"
        }
        self.testapp.post_json(url, params=params, status=401, extra_environ=anonyous_env)
        self.testapp.post_json(url, params=params, status=403, extra_environ=other_env)
        self.testapp.post_json(url, params=params, status=403, extra_environ=admin_env)
        res = self.testapp.post_json(url, params=params, status=201, extra_environ=owner_env).json_body
        assert_that(res, has_entries({'title': 'go to school'}))
        EVENT_ID = res['ID']

        # Read event.
        event_url = "%s/%s" % (url, EVENT_ID)
        self.testapp.get(event_url, status=401, extra_environ=anonyous_env)
        self.testapp.get(event_url, status=403, extra_environ=other_env)
        self.testapp.get(event_url, status=403, extra_environ=admin_env)
        self.testapp.get(event_url, status=200, extra_environ=friend_env)
        res = self.testapp.get(event_url, status=200, extra_environ=owner_env).json_body
        assert_that(res, has_entries({'MimeType': 'application/vnd.nextthought.calendar.friendslistcalendarevent'}))

        # Update event.
        self.testapp.put_json(event_url, params=params, status=401, extra_environ=anonyous_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=other_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=admin_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=friend_env)
        self.testapp.put_json(event_url, params=params, status=200, extra_environ=owner_env)

        # Delete Event.
        self.testapp.delete(event_url, status=401, extra_environ=anonyous_env)
        self.testapp.delete(event_url, status=403, extra_environ=other_env)
        self.testapp.delete(event_url, status=403, extra_environ=admin_env)
        self.testapp.delete(event_url, status=403, extra_environ=friend_env)
        self.testapp.delete(event_url, status=204, extra_environ=owner_env)

        # Friend created event.
        res = self.testapp.post_json(url, params=params, status=201, extra_environ=friend_env).json_body
        assert_that(res, has_entries({'title': 'go to school'}))
        EVENT_ID = res['ID']

        with mock_dataserver.mock_db_trans(self.ds):
            assert_that(IFriendsListCalendar(friends), has_length(1))

        # Read
        event_url = "%s/%s" % (url, EVENT_ID)
        self.testapp.get(event_url, status=401, extra_environ=anonyous_env)
        self.testapp.get(event_url, status=403, extra_environ=other_env)
        self.testapp.get(event_url, status=403, extra_environ=admin_env)
        self.testapp.get(event_url, status=200, extra_environ=owner_env)
        self.testapp.get(event_url, status=200, extra_environ=another_friend_env)
        res = self.testapp.get(event_url, status=200, extra_environ=friend_env).json_body
        assert_that(res, has_entries({'MimeType': 'application/vnd.nextthought.calendar.friendslistcalendarevent'}))

        # Update event.
        self.testapp.put_json(event_url, params=params, status=401, extra_environ=anonyous_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=other_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=admin_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=owner_env)
        self.testapp.put_json(event_url, params=params, status=403, extra_environ=another_friend_env)
        self.testapp.put_json(event_url, params=params, status=200, extra_environ=friend_env)

        # Delete
        self.testapp.delete(event_url, status=401, extra_environ=anonyous_env)
        self.testapp.delete(event_url, status=403, extra_environ=other_env)
        self.testapp.delete(event_url, status=403, extra_environ=admin_env)
        self.testapp.delete(event_url, status=403, extra_environ=owner_env)
        self.testapp.delete(event_url, status=403, extra_environ=another_friend_env)
        self.testapp.delete(event_url, status=204, extra_environ=friend_env)

        with mock_dataserver.mock_db_trans(self.ds):
            assert_that(IFriendsListCalendar(friends), has_length(0))


class TestUserCompositeCalendarView(CalendarLayerTest):

    def _create_group(self, username):
        params  = {
            "MimeType":"application/vnd.nextthought.dynamicfriendslist",
            "Username":"ohyeah-%s_d2a97129-6cc8-4f8a-b883-edcd78ade177" % username,
            "alias":"ohyeah",
            "friends":[],
            "IsDynamicSharing":True
        }
        url = '/dataserver2/users/%s/Groups' % username
        result = self.testapp.post_json(url, params=params, status=201, extra_environ=self._make_extra_environ(username=username)).json_body
        return result

    @WithSharedApplicationMockDS(testapp=True, users=(u'owner001', u'community_member001', u'group_memeber001', u'admin001@nextthought.com', u'other'))
    def test_my_calendar_view(self):
        # Return calendar events from user, community, group and enrollment courses.
        owner_env = self._make_extra_environ(username=u'owner001')
        community_member_env = self._make_extra_environ(username=u'community_member001')
        group_memeber_env = self._make_extra_environ(username=u'group_memeber001')
        admin_env = self._make_extra_environ(username=u'admin001@nextthought.com')

        url = '/dataserver2/users/owner001/Calendars/@@events'
        self.testapp.get(url, extra_environ=admin_env)
        self.testapp.get(url, status=403, extra_environ=community_member_env)
        self.testapp.get(url, status=403, extra_environ=group_memeber_env)
        self.testapp.get(url, status=401, extra_environ=self._make_extra_environ(username=None))
        result = self.testapp.get(url, status=200, extra_environ=owner_env).json_body
        assert_that(result, has_entries({'Total': 0, 'Items': has_length(0)}))

        # create group
        res = self._create_group('owner001')
        group_name = res['realname']

        community_name = u'test.community.com'
        with mock_dataserver.mock_db_trans(self.ds):
            community = Community.create_community(self.ds, username=community_name)
            assert_that(ICommunityCalendar(community), not_none())

            for username in (u'owner001', u'community_member001', u'admin001@nextthought.com'):
                user = User.get_user(username)
                user.record_dynamic_membership(community)

            # add user event
            IUserCalendar(User.get_user(u'owner001')).store_event(UserCalendarEvent(title=u'myself'))
            IUserCalendar(User.get_user(u'community_member001')).store_event(UserCalendarEvent(title=u'community_member_self'))
            IUserCalendar(User.get_user(u'group_memeber001')).store_event(UserCalendarEvent(title=u'group_member_self'))

            # add community events
            ICommunityCalendar(community).store_event(CommunityCalendarEvent(title=u'community event title'))

            # add Group events.
            user = User.get_user('owner001')
            group = user.friendsLists[group_name]
            IFriendsListCalendar(group).store_event(FriendsListCalendarEvent(title=u'group event title'))

            group.addFriend(User.get_user(u'group_memeber001'))

        # owner
        result = self.testapp.get(url, status=200, extra_environ=owner_env).json_body
        assert_that(result, has_entries({'Total': 3, 'Items': has_length(3)}))
        assert_that([x['title'] for x in result['Items']], contains_inanyorder(u'myself', u'community event title', u'group event title'))

        # community memeber
        url = '/dataserver2/users/community_member001/Calendars/@@events'
        result = self.testapp.get(url, status=200, extra_environ=community_member_env).json_body
        assert_that(result, has_entries({'Total': 2, 'Items': has_length(2)}))
        assert_that([x['title'] for x in result['Items']], contains_inanyorder(u'community_member_self', u'community event title'))

        # group member
        url = '/dataserver2/users/group_memeber001/Calendars/@@events'
        result = self.testapp.get(url, status=200, extra_environ=group_memeber_env).json_body
        assert_that(result, has_entries({'Total': 2, 'Items': has_length(2)}))
        assert_that([x['title'] for x in result['Items']], contains_inanyorder(u'group_member_self', u'group event title'))

        # admin(community member)
        url = '/dataserver2/users/admin001@nextthought.com/Calendars/@@events'
        result = self.testapp.get(url, status=200, extra_environ=admin_env).json_body
        assert_that(result, has_entries({'Total': 1, 'Items': has_length(1)}))
        assert_that([x['title'] for x in result['Items']], contains_inanyorder(u'community event title'))

        # other user, nothing
        url = '/dataserver2/users/other/Calendars/@@events'
        result = self.testapp.get(url, status=200, extra_environ=self._make_extra_environ(username=u'other')).json_body
        assert_that(result, has_entries({'Total': 0, 'Items': has_length(0)}))
