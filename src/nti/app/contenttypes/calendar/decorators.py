#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ
from nti.contenttypes.calendar.interfaces import ICalendarEventAttendanceContainer
from zope import component
from zope import interface

from nti.app.contenttypes.calendar import CONTENTS_VIEW_NAME
from nti.app.contenttypes.calendar import EXPORT_VIEW_NAME

from nti.app.products.courseware.interfaces import ACT_RECORD_EVENT_ATTENDANCE

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver._util import link_belongs_to_user as link_belongs_to_context

from nti.appserver.pyramid_authorization import has_permission

from nti.appserver.pyramid_renderers_edit_link_decorator import EditLinkDecorator

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent
from nti.contenttypes.calendar.interfaces import IUserCalendarEventAttendance

from nti.dataserver.authorization import ACT_READ
from nti.dataserver.authorization import ACT_UPDATE

from nti.dataserver.users import User

from nti.externalization import to_external_object

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.externalization.singleton import Singleton

from nti.links.links import Link

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICalendar)
@interface.implementer(IExternalObjectDecorator)
class _CalendarEditLinkDecorator(EditLinkDecorator):

    def _has_permission(self, context):
        return has_permission(ACT_UPDATE, context, self.request)


@component.adapter(ICalendar)
@interface.implementer(IExternalObjectDecorator)
class _CalendarLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, context, external):
        return has_permission(ACT_READ, context, self.request)

    def _do_decorate_external(self, context, external):
        _links = external.setdefault(StandardExternalFields.LINKS, [])
        for rel in (CONTENTS_VIEW_NAME, EXPORT_VIEW_NAME):
            _link = Link(context,
                         rel=rel,
                         elements=('@@'+rel, ),
                         method='GET')
            link_belongs_to_context(_link, context)
            _links.append(_link)


@component.adapter(ICalendarEvent)
@interface.implementer(IExternalObjectDecorator)
class _CalendarEventEditLinkDecorator(EditLinkDecorator):

    def _has_permission(self, context):
        return has_permission(ACT_UPDATE, context, self.request)


@component.adapter(ICalendarEvent)
@interface.implementer(IExternalMappingDecorator)
class _CalendarEventDecorator(Singleton):

    def decorateExternalMapping(self, context, result):
        calendar = ICalendar(context, None)
        result['ContainerId'] = getattr(calendar, 'ntiid', None)


@component.adapter(IUserCalendarEventAttendance)
@interface.implementer(IExternalObjectDecorator)
class UserCalendarEventAttendanceDecorator(Singleton):

    def decorateExternalObject(self, context, result):
        user = User.get_user(context.Username)
        if user is not None:
            result.pop('Username')
            result['User'] = to_external_object(user)


@component.adapter(IUserCalendarEventAttendance)
@interface.implementer(IExternalObjectDecorator)
class UserCalendarEventAttendanceEditLinkDecorator(EditLinkDecorator):

    def _predicate(self, context, result):
        return EditLinkDecorator._predicate(self, context, result)

    def _has_permission(self, context):
        return has_permission(ACT_RECORD_EVENT_ATTENDANCE, context, self.request)


@component.adapter(IUserCalendarEventAttendance)
@interface.implementer(IExternalObjectDecorator)
class UserCalendarEventAttendanceDeleteLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _has_permission(self, context):
        return has_permission(ACT_RECORD_EVENT_ATTENDANCE, context, self.request)

    def _predicate(self, context, result):
        return AbstractAuthenticatedRequestAwareDecorator._predicate(self, context, result) \
            and self._has_permission(context)

    def _do_decorate_external(self, context, result):
        links = result.setdefault(LINKS, [])
        links.append(
            Link(context, rel='delete', method='DELETE')
        )


@component.adapter(ICalendarEvent)
@interface.implementer(IExternalObjectDecorator)
class CalendarEventAttendanceLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _has_permission(self, context):
        return has_permission(ACT_RECORD_EVENT_ATTENDANCE, context, self.request)

    def _predicate(self, context, result):
        return AbstractAuthenticatedRequestAwareDecorator._predicate(self, context, result) \
            and self._has_permission(context)

    def _do_decorate_external(self, context, result):
        attendance_container = ICalendarEventAttendanceContainer(context)
        if attendance_container is not None:
            links = result.setdefault(LINKS, [])
            links.append(
                Link(attendance_container, rel='record-attendance', method='POST')
            )
            links.append(
                Link(attendance_container, rel='list-attendance', method='GET')
            )
