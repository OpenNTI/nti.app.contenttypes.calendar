#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.container.constraints import contains

from zope.location.interfaces import IContained

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent


class IEntityCalendarEvent(ICalendarEvent):
    pass


class IEntityCalendar(ICalendar, IContained):
    pass


class IUserCalendarEvent(IEntityCalendarEvent):
    pass


class IUserCalendar(IEntityCalendar):
    """
    A calendar that should be annotated on the user object.
    """
    contains(IUserCalendarEvent)
    __setitem__.__doc__ = None
