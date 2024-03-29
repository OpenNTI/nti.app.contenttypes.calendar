#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from datetime import datetime

from pyramid.interfaces import IRequest

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.security.interfaces import IPrincipal

from nti.app.authentication import get_remote_user

from nti.app.contenttypes.calendar import EXPORT_ATTENDANCE_VIEW

from nti.app.contenttypes.calendar.authorization import ACT_RECORD_EVENT_ATTENDANCE
from nti.app.contenttypes.calendar.authorization import ACT_VIEW_EVENT_ATTENDANCE

from nti.app.contenttypes.calendar.interfaces import DuplicateAttendeeError
from nti.app.contenttypes.calendar.interfaces import ICalendarEventAttendanceLinkSource
from nti.app.contenttypes.calendar.interfaces import ICalendarEventAttendanceManager
from nti.app.contenttypes.calendar.interfaces import IEventUserSearchHit
from nti.app.contenttypes.calendar.interfaces import InvalidAttendeeError

from nti.appserver.pyramid_authorization import has_permission as app_has_permission

from nti.contenttypes.calendar.attendance import UserCalendarEventAttendance

from nti.contenttypes.calendar.interfaces import ICalendarDynamicEvent
from nti.contenttypes.calendar.interfaces import ICalendarEvent
from nti.contenttypes.calendar.interfaces import ICalendarEventAttendanceContainer
from nti.contenttypes.calendar.interfaces import IUserCalendarEventAttendance

from nti.coremetadata.interfaces import IUser

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.authorization_acl import has_permission

from nti.links import Link

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured


@component.adapter(ICalendarEvent)
@interface.implementer(ICalendarEventAttendanceManager)
class DefaultEventAttendanceManager(object):

    def __init__(self, context):
        self.context = context

    def can_attend(self, user):
        return has_permission(ACT_READ, self.context, user.username)

    def attendee_search_predicate(self, user):
        return user == self.context.creator

    @Lazy
    def container(self):
        return ICalendarEventAttendanceContainer(self.context)

    def add_attendee(self, user, creator=None, registration_time=None):
        attendance = UserCalendarEventAttendance()
        attendance.creator = creator or get_remote_user().username
        attendance.registrationTime = registration_time or datetime.utcnow()

        if not self.can_attend(user):
            raise InvalidAttendeeError(u"Registration forbidden for user %s to this event." % user.username)

        try:
            return self.container.add_attendance(user, attendance)
        except KeyError:
            raise DuplicateAttendeeError(u"User %s already registered." % user.username)


@component.adapter(ICalendarEvent, IRequest)
@interface.implementer(ICalendarEventAttendanceLinkSource)
class DefaultCalendarEventAttendanceLinkSource(object):

    def __init__(self, event, request):
        self.event = event
        self.request = request

    def _has_create_permission(self, context):
        return app_has_permission(ACT_RECORD_EVENT_ATTENDANCE, context, self.request)

    def _has_list_permission(self, context):
        return app_has_permission(ACT_VIEW_EVENT_ATTENDANCE, context, self.request)

    def search_links(self):
        return (Link(self.event, elements=('UserSearch',),
                    rel='search-possible-attendees'),)

    def links(self):
        result = []

        if ICalendarDynamicEvent.providedBy(self.event):
            return result

        attendance_container = ICalendarEventAttendanceContainer(self.event)
        if attendance_container is not None:
            if self._has_create_permission(attendance_container):
                result.append(
                    Link(attendance_container, rel='record-attendance', method='POST')
                )

                for search_link in self.search_links() or ():
                    result.append(search_link)

            if self._has_list_permission(attendance_container):
                result.append(
                    Link(attendance_container, rel='list-attendance', method='GET')
                )

                result.append(
                    Link(attendance_container,
                         rel='export-attendance',
                         elements=('@@%s' % EXPORT_ATTENDANCE_VIEW,),
                         method='GET')
                )

        return result


@component.adapter(ICalendarEventAttendanceContainer)
@interface.implementer(ICalendarEventAttendanceManager)
def container_to_attendance_manager(container):
    return ICalendarEventAttendanceManager(ICalendarEvent(container))


@component.adapter(ICalendarEvent, IUser)
@interface.implementer(IUserCalendarEventAttendance)
def user_calendar_event_attendance(event, user):
    attendance_container = ICalendarEventAttendanceContainer(event)
    principal_id = IPrincipal(user).id
    return attendance_container.get(principal_id)


@interface.implementer(IEventUserSearchHit)
class EventUserSearchHit(SchemaConfigured):
    createDirectFieldProperties(IEventUserSearchHit)

    __external_can_create__ = False

    def __init__(self, **kwargs):
        SchemaConfigured.__init__(self, **kwargs)


@component.adapter(IUser, ICalendarEvent)
@interface.implementer(IEventUserSearchHit)
def get_search_hit(user, event):
    return EventUserSearchHit(User=user, Event=event)
