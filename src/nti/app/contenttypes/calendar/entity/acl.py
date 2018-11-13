#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from nti.app.authentication import get_remote_user

from nti.app.contenttypes.calendar.entity.interfaces import ICommunityCalendar
from nti.app.contenttypes.calendar.entity.interfaces import IFriendsListCalendar

from nti.dataserver.authorization import ACT_READ
from nti.dataserver.authorization import ACT_CREATE
from nti.dataserver.authorization import ROLE_ADMIN
from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.authorization_acl import acl_from_aces
from nti.dataserver.authorization_acl import ace_allowing

from nti.dataserver.interfaces import ACE_DENY_ALL
from nti.dataserver.interfaces import ALL_PERMISSIONS
from nti.dataserver.interfaces import AUTHENTICATED_GROUP_NAME
from nti.dataserver.interfaces import IACLProvider


@interface.implementer(IACLProvider)
@component.adapter(ICommunityCalendar)
class _CommunityCalendarACLProvider(object):

    def __init__(self, context):
        self.context = context

    @property
    def __parent__(self):
        # See comments in nti.dataserver.authorization_acl:has_permission
        return self.context.__parent__

    @Lazy
    def __acl__(self):
        aces = [ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, type(self)),
                ace_allowing(ROLE_SITE_ADMIN, ALL_PERMISSIONS, type(self))]

        # Community members can read.
        user = get_remote_user()
        if user is not None:
            if self.__parent__.public or user in self.__parent__:
                aces.append(ace_allowing(user.username, ACT_READ, type(self)))

        aces.append(ACE_DENY_ALL)
        result = acl_from_aces(aces)
        return result


@interface.implementer(IACLProvider)
@component.adapter(IFriendsListCalendar)
class _FriendsListCalendarACLProvider(object):

    def __init__(self, context):
        self.context = context

    @property
    def __parent__(self):
        # See comments in nti.dataserver.authorization_acl:has_permission
        return self.context.__parent__

    @property
    def _creator(self):
        return getattr(self.__parent__, 'creator', None)

    @Lazy
    def __acl__(self):
        aces = []
        if self._creator:
            aces.append(ace_allowing(self._creator, ALL_PERMISSIONS, type(self)))

        # Friends can create and read.
        user = get_remote_user()
        if      user is not None \
            and self.__parent__ is not None \
            and user in self.__parent__:
            for perm in (ACT_READ, ACT_CREATE):
                aces.append(ace_allowing(user.username, perm, type(self)))

        aces.append(ACE_DENY_ALL)
        result = acl_from_aces(aces)
        return result
