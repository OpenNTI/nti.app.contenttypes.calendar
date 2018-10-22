#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.appserver.pyramid_authorization import has_permission

from nti.appserver.pyramid_renderers_edit_link_decorator import EditLinkDecorator

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent

from nti.dataserver.authorization import ACT_UPDATE

from nti.externalization.interfaces import IExternalObjectDecorator


@component.adapter(ICalendar)
@interface.implementer(IExternalObjectDecorator)
class _CalendarEditLinkDecorator(EditLinkDecorator):

    def _has_permission(self, context):
        return has_permission(ACT_UPDATE, context, self.request)


@component.adapter(ICalendarEvent)
@interface.implementer(IExternalObjectDecorator)
class _CalendarEventEditLinkDecorator(EditLinkDecorator):

    def _has_permission(self, context):
        return has_permission(ACT_UPDATE, context, self.request)
