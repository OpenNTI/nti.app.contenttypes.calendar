#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.app.contenttypes.calendar import CONTENTS_VIEW_NAME
from nti.app.contenttypes.calendar import EXPORT_VIEW_NAME

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver._util import link_belongs_to_user as link_belongs_to_context

from nti.appserver.pyramid_authorization import has_permission

from nti.appserver.pyramid_renderers_edit_link_decorator import EditLinkDecorator

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent

from nti.dataserver.authorization import ACT_READ
from nti.dataserver.authorization import ACT_UPDATE

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.externalization.singleton import Singleton

from nti.links.links import Link


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
