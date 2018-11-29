#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from nti.appserver.workspaces.interfaces import ICollection

from nti.dataserver.interfaces import IACLProvider


class ICalendarACLProvider(IACLProvider):
    """
    An ACL provider giving permissions beneath an ICalendar.
    Typically adapted from (ICalendar, *)
    """


class ICalendarCollection(ICollection):
    """
    A collection containing data for calendar events.
    """
