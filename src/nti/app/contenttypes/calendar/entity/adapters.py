#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.interfaces import IRequest

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation.interfaces import IAnnotations

from zope.traversing.interfaces import IPathAdapter

from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendar
from nti.app.contenttypes.calendar.entity.interfaces import ICommunityCalendar
from nti.app.contenttypes.calendar.entity.interfaces import IFriendsListCalendar

from nti.app.contenttypes.calendar.entity.model import UserCalendar
from nti.app.contenttypes.calendar.entity.model import CommunityCalendar
from nti.app.contenttypes.calendar.entity.model import FriendsListCalendar

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ICommunity
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

logger = __import__('logging').getLogger(__name__)

KEY = u'Calendar'


def _create_annotation(parent, calendar_factory, key=KEY, create=True):
    result = None
    annotations = IAnnotations(parent)
    try:
        result = annotations[key]
    except KeyError:
        if create:
            result = calendar_factory()
            annotations[key] = result
            result.__name__ = key
            result.__parent__ = parent
            connection = IConnection(parent, None)
            if connection is not None:
                # pylint: disable=too-many-function-args
                connection.add(result)
    return result


@component.adapter(IUser)
@interface.implementer(IUserCalendar)
def _UserCalendarFactory(user, create=True):
    return _create_annotation(user, UserCalendar, create=create)


@component.adapter(ICommunity)
@interface.implementer(ICommunityCalendar)
def _CommunityCalendarFactory(community, create=True):
    return _create_annotation(community, CommunityCalendar, create=create)


@component.adapter(IDynamicSharingTargetFriendsList)
@interface.implementer(IFriendsListCalendar)
def _FriendsListCalendarFactory(friendsList, create=True):
    return _create_annotation(friendsList, FriendsListCalendar, create=create)


@interface.implementer(IPathAdapter)
@component.adapter(IUser, IRequest)
def _UserCalendarPathAdapter(context, request):
    return _UserCalendarFactory(context)


@interface.implementer(IPathAdapter)
@component.adapter(ICommunity, IRequest)
def _CommunityCalendarPathAdapter(context, request):
    return _CommunityCalendarFactory(context)


@interface.implementer(IPathAdapter)
@component.adapter(IDynamicSharingTargetFriendsList, IRequest)
def _FriendsListCalendarPathAdapter(context, request):
    return _FriendsListCalendarFactory(context)
