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

from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendar
from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendarEvent

from nti.contenttypes.calendar.model import Calendar
from nti.contenttypes.calendar.model import CalendarEvent

from nti.dataserver.authorization_acl import acl_from_aces

from nti.property.property import LazyOnClass

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
