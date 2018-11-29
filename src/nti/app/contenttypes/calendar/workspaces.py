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

from zope.container.contained import Contained

from nti.app.contenttypes.calendar import CALENDARS
from nti.app.contenttypes.calendar import EVENTS_VIEW_NAME

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.appserver.workspaces.interfaces import IUserWorkspace

from nti.links.links import Link

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ICalendarCollection)
@component.adapter(IUserWorkspace)
class CalendarCollection(Contained):

    name = CALENDARS
    __name__ = CALENDARS

    accepts = ()

    def __init__(self, user):
        self.__parent__ = user

    @property
    def user(self):
        return self.__parent__

    @property
    def links(self):
        result = []
        result.append( Link(self.user,
                            rel=EVENTS_VIEW_NAME,
                            elements=(self.__name__, '@@'+EVENTS_VIEW_NAME,),
                            method='GET'))
        return result


def _calendar_collection_factory(user_workspace):
    return CalendarCollection(user_workspace.user)
