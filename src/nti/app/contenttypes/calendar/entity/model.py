#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.container.contained import Contained

from nti.app.authentication import get_remote_user

from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendar
from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendarEvent
from nti.app.contenttypes.calendar.entity.interfaces import ICommunityCalendar
from nti.app.contenttypes.calendar.entity.interfaces import ICommunityCalendarEvent
from nti.app.contenttypes.calendar.entity.interfaces import IFriendsListCalendar
from nti.app.contenttypes.calendar.entity.interfaces import IFriendsListCalendarEvent

from nti.contenttypes.calendar.model import Calendar
from nti.contenttypes.calendar.model import CalendarEvent

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.authorization_acl import acl_from_aces
from nti.dataserver.authorization_acl import ace_allowing

from nti.dataserver.interfaces import ACE_DENY_ALL
from nti.dataserver.interfaces import ALL_PERMISSIONS
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

from nti.property.property import LazyOnClass

from nti.traversal.traversal import find_interface

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IUserCalendar)
class UserCalendar(Calendar, Contained):

    __external_class_name__ = "UserCalendar"
    mimeType = mime_type = "application/vnd.nextthought.calendar.usercalendar"


@interface.implementer(IUserCalendarEvent)
class UserCalendarEvent(CalendarEvent):

    __external_class_name__ = "UserCalendarEvent"
    mimeType = mime_type = "application/vnd.nextthought.calendar.usercalendarevent"

    @LazyOnClass
    def __acl__(self):
        # If we don't have this, it would derive one from ICreated, rather than its parent.
        return acl_from_aces([])


@interface.implementer(ICommunityCalendar)
class CommunityCalendar(Calendar, Contained):

    __external_class_name__ = "CommunityCalendar"
    mimeType = mime_type = "application/vnd.nextthought.calendar.communitycalendar"


@interface.implementer(ICommunityCalendarEvent)
class CommunityCalendarEvent(CalendarEvent):

    __external_class_name__ = "CommunityCalendarEvent"
    mimeType = mime_type = "application/vnd.nextthought.calendar.communitycalendarevent"

    @LazyOnClass
    def __acl__(self):
        # If we don't have this, it would derive one from ICreated, rather than its parent.
        return acl_from_aces([])


@interface.implementer(IFriendsListCalendar)
class FriendsListCalendar(Calendar, Contained):

    __external_class_name__ = "FriendsListCalendar"
    mimeType = mime_type = "application/vnd.nextthought.calendar.friendslistcalendar"


@interface.implementer(IFriendsListCalendarEvent)
class FriendsListCalendarEvent(CalendarEvent):

    __external_class_name__ = "FriendsListCalendarEvent"
    mimeType = mime_type = "application/vnd.nextthought.calendar.friendslistcalendarevent"

    def __acl__(self):
        aces = []
        if self.creator:
            aces.append(ace_allowing(self.creator, ALL_PERMISSIONS, type(self)))

        # creator of the FriendsList or friend has read permission
        user = get_remote_user()
        friends_list = find_interface(self, IDynamicSharingTargetFriendsList, strict=False)
        if user is not None and friends_list is not None:
            if user == friends_list.creator or user in friends_list:
                aces.append(ace_allowing(user.username, ACT_READ, type(self)))

        aces.append(ACE_DENY_ALL)
        return acl_from_aces(aces)
