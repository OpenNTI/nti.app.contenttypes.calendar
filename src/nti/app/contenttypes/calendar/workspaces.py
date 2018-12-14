#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.threadlocal import get_current_request

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from zope.security.interfaces import IPrincipal

from nti.app.contenttypes.calendar import CALENDARS
from nti.app.contenttypes.calendar import EVENTS_VIEW_NAME
from nti.app.contenttypes.calendar import EXPORT_VIEW_NAME
from nti.app.contenttypes.calendar import GENERATE_FEED_URL

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.appserver.workspaces.interfaces import IUserWorkspace

from nti.contenttypes.calendar.interfaces import ICalendarProvider

from nti.dataserver.authorization import ROLE_ADMIN

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces

from nti.dataserver.interfaces import ACE_DENY_ALL
from nti.dataserver.interfaces import ALL_PERMISSIONS

from nti.externalization.interfaces import LocatedExternalList

from nti.links.links import Link

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUserWorkspace)
@interface.implementer(ICalendarCollection)
class CalendarCollection(Contained):

    name = CALENDARS
    __name__ = CALENDARS

    accepts = ()

    def __init__(self, workspace):
        # We get a user here on path adapter
        self.__parent__ = workspace.user

    @property
    def user(self):
        return self.__parent__

    @Lazy
    def __acl__(self):
        # Only the user has access to this calendar
        aces = [ace_allowing(IPrincipal(self.user), ALL_PERMISSIONS, type(self)),
                ace_allowing(ROLE_ADMIN, ALL_PERMISSIONS, type(self))]
        aces.append(ACE_DENY_ALL)
        return acl_from_aces(aces)

    @Lazy
    def _request(self):
        return getattr(self, 'request', None) or get_current_request()

    def _context_ntiids(self):
        result = self._request.params.getall('context_ntiids') if self._request else None
        return [x for x in result or () if x]

    def _excluded_context_ntiids(self):
        result = self._request.params.getall('excluded_context_ntiids') if self._request else None
        return [x for x in result or () if x]

    @Lazy
    def calendars(self):
        """
        Return a dict of course catalog entries the user is not enrolled
        in and that are available to be enrolled in.
        """
        result = LocatedExternalList()
        providers = component.subscribers((self.user,),
                                          ICalendarProvider)
        for x in providers or ():
            result.extend(x.iter_calendars(context_ntiids=self._context_ntiids(),
                                           excluded_context_ntiids=self._excluded_context_ntiids()))
        return result

    @Lazy
    def container(self):
        container = self.calendars
        container.__name__ = self.__name__
        container.__parent__ = self.__parent__
        container.lastModified = 0
        return container

    @property
    def links(self):
        result = []
        for rel in (EVENTS_VIEW_NAME, EXPORT_VIEW_NAME, GENERATE_FEED_URL):
            result.append( Link(self.user,
                                rel=rel,
                                elements=(self.__name__,
                                          '@@%s' % rel,),
                                method='GET'))
        return result


def _calendar_collection_factory(user_workspace):
    return ICalendarCollection(user_workspace, None)


@component.adapter(IUserWorkspace)
@interface.implementer(ICalendarCollection)
def _calendar_collection_adapter(workspace):
    """
    Adapter to the :class:`ICalendarCollection`; this is the default
    adapter.
    """
    result = CalendarCollection(workspace)
    return result


@component.adapter(IUserWorkspace)
@interface.implementer(ICalendarCollection)
def _empty_calendar_collection_adapter(unused_workspace):
    """
    Empty adapter to the :class:`ICalendarCollection` for sites that
    may not want this functionality.
    """
    pass
