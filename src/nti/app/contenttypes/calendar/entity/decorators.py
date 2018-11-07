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
from nti.app.contenttypes.calendar.entity.interfaces import ICommunityCalendar
from nti.app.contenttypes.calendar.entity.interfaces import IFriendsListCalendar

from nti.app.renderers.decorators import AbstractRequestAwareDecorator
from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver._util import link_belongs_to_user as link_belongs_to_context

from nti.appserver.pyramid_authorization import has_permission

from nti.dataserver.authorization import ACT_READ

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ICommunity
from nti.dataserver.interfaces import IDynamicSharingTargetFriendsList

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
            _link = Link(calendar, rel='Calendar')
            link_belongs_to_context(_link, context)
            _links.append(_link)


@component.adapter(ICommunity)
@interface.implementer(IExternalObjectDecorator)
class _CommunityCalendarLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):

    def _predicate(self, context, external):
        return has_permission(ACT_READ, context, self.request)

    def _do_decorate_external(self, context, external):
        _links = external.setdefault(StandardExternalFields.LINKS, [])
        calendar = ICommunityCalendar(context, None)
        if calendar is not None:
            _link = Link(calendar, rel='Calendar')
            link_belongs_to_context(_link, context)
            _links.append(_link)


@component.adapter(IDynamicSharingTargetFriendsList)
@interface.implementer(IExternalObjectDecorator)
class _FriendsListCalendarLinkDecorator(AbstractRequestAwareDecorator):

    def _do_decorate_external(self, context, external):
        _links = external.setdefault(StandardExternalFields.LINKS, [])
        calendar = IFriendsListCalendar(context, None)
        if calendar is not None:
            _link = Link(calendar, rel='Calendar')
            link_belongs_to_context(_link, context)
            _links.append(_link)
