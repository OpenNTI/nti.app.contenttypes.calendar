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

from nti.app.contenttypes.calendar.utils import generate_calendar_event_url

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent
from nti.contenttypes.calendar.interfaces import ICalendarEventURLProvider

from nti.traversal.traversal import find_interface

logger = __import__('logging').getLogger(__name__)

@component.adapter(ICalendarEvent)
@interface.implementer(ICalendar)
def calendar_event_to_calendar(event):
    return find_interface(event, ICalendar, strict=False)


@component.adapter(ICalendarEvent)
@interface.implementer(ICalendarEventURLProvider)
class CalendarEventURLProvider(object):

    def __init__(self, calendar_event):
        self.calendar_event = calendar_event

    def __call__(self):
        return generate_calendar_event_url(self.calendar_event)
