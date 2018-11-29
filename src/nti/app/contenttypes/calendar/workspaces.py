#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from zope.location.interfaces import ILocation
from zope.location.interfaces import IContained

from nti.dataserver.authentication import  get_current_request

from nti.app.contenttypes.calendar import CALENDARS

from nti.app.contenttypes.calendar.entity import MY_CALENDAR_VIEW_NAME

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.appserver.workspaces.interfaces import IUserService
from nti.appserver.workspaces.interfaces import IUserWorkspace

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IDataserverFolder

from nti.links.links import Link

from nti.property.property import alias


@interface.implementer(ICalendarCollection)
@component.adapter(IUserWorkspace)
class _CalendarCollection(Contained):

    name = CALENDARS
    __name__ = CALENDARS

    accepts = ()

    def __init__(self, user_workspace):
        self.__parent__ = user_workspace

    @property
    def user(self):
        return getattr(self.__parent__, 'user', None)

    @property
    def links(self):
        result = []
        result.append( Link(self.user,
                            rel=MY_CALENDAR_VIEW_NAME,
                            elements=('@@'+MY_CALENDAR_VIEW_NAME,),
                            method='GET'))
        return result
