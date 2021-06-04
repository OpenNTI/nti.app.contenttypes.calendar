#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime

from zope import component
from zope import interface

from nti.app.authentication import get_remote_user

from nti.app.contenttypes.calendar.interfaces import DuplicateAttendeeError
from nti.app.contenttypes.calendar.interfaces import ICalendarEventAttendanceManager
from nti.app.contenttypes.calendar.interfaces import InvalidAttendeeError

from nti.contenttypes.calendar.attendance import UserCalendarEventAttendance
from nti.contenttypes.calendar.interfaces import ICalendarEventAttendanceContainer

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.authorization_acl import has_permission


@component.adapter(ICalendarEventAttendanceContainer)
@interface.implementer(ICalendarEventAttendanceManager)
class DefaultEventAttendanceManager(object):

    def __init__(self, context):
        self.context = context

    def can_attend(self, user):
        return has_permission(ACT_READ, self.context, user.username)

    def add_attendee(self, user, creator=None, registration_time=None):
        attendance = UserCalendarEventAttendance()
        attendance.creator = creator or get_remote_user().username
        attendance.registrationTime = registration_time or datetime.utcnow()

        if not self.can_attend(user):
            raise InvalidAttendeeError(u"Registration forbidden for user %s to this event." % user.username)

        try:
            return self.context.add_attendance(user, attendance)
        except KeyError:
            raise DuplicateAttendeeError(u"User %s already registered." % user.username)
