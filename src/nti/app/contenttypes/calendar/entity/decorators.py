#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendar

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver._util import link_belongs_to_user as link_belongs_to_context

from nti.appserver.pyramid_authorization import has_permission

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.interfaces import IUser

from nti.externalization.interfaces import IExternalObjectDecorator
from nti.externalization.interfaces import StandardExternalFields

from nti.links.links import Link


@component.adapter(IUser)
@interface.implementer(IExternalObjectDecorator)
class _UserCalendarLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, context, external):
        # should we only allow owner?
        return has_permission(ACT_READ, context, self.request)

    def _do_decorate_external(self, context, external):
        _links = external.setdefault(StandardExternalFields.LINKS, [])
        calendar = IUserCalendar(context, None)
        if calendar is not None:
            _link = Link(calendar,
                         rel='UserCalendar',
                         method='GET')
            link_belongs_to_context(_link, context)
            _links.append(_link)
