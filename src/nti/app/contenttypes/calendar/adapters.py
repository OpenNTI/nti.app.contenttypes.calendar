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

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent

from nti.traversal.traversal import find_interface

logger = __import__('logging').getLogger(__name__)

@component.adapter(ICalendarEvent)
@interface.implementer(ICalendar)
def calendar_event_to_calendar(event):
    return find_interface(event, ICalendar, strict=False)
