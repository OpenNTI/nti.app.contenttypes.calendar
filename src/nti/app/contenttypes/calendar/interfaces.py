#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from zope import interface

from nti.appserver.workspaces.interfaces import IContainerCollection

from nti.dataserver.interfaces import IACLProvider


class ICalendarACLProvider(IACLProvider):
    """
    An ACL provider giving permissions beneath an ICalendar.
    Typically adapted from (ICalendar, *)
    """


class ICalendarCollection(IContainerCollection):
    """
    A collection containing calendars.
    """


class IAdminCalendarCollection(ICalendarCollection):
    """
    A collection containing calendars the user is an administrator of.
    """


class ICalendarEventUIDProvider(interface.Interface):
    """
    An object that can be adapted from an :class:`ICalendarEvent`, and
    return an appropriate uid used for calendar feed exporting.
    """
    def __call__():
        """
        Return an uid for :class: `ICalendarEvent`.
        """


class ICalendarEventAttendanceManager(interface.Interface):
    """
    Handles the logic for adding users as attendee for an event
    """

    def add_attendee(user, creator=None, registration_time=None):
        """
        Add the user provided as an attendee to the event.

        :return: Newly added IUserCalendarEventAttendance record
        """


class DuplicateAttendeeError(Exception):
    pass


class InvalidAttendeeError(Exception):
    """
    Indication that an attempt was made to add an attendee to an event
    they're not allowed to attend (e.g. a course event they're not enrolled
    in).
    """
