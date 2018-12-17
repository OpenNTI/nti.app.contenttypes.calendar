#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid import httpexceptions as hexc

from pyramid.threadlocal import get_current_request

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from zope.i18n import translate

from zope.security.interfaces import IPrincipal

from nti.app.contenttypes.calendar import CALENDARS
from nti.app.contenttypes.calendar import EVENTS_VIEW_NAME
from nti.app.contenttypes.calendar import EXPORT_VIEW_NAME
from nti.app.contenttypes.calendar import MessageFactory as _
from nti.app.contenttypes.calendar import GENERATE_FEED_URL

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.app.externalization.error import raise_json_error

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

    def _ntiids(self, name):
        result = None
        if self._request:
            if name in self._request.params:
                result = self._request.params.getall(name)
            else:
                try:
                    body = self._request.json_body
                    result = body.get(name)
                except ValueError:
                    pass
                else:
                    if result is not None and not isinstance(result, list):
                        raise_json_error(self._request,
                                         hexc.HTTPUnprocessableEntity,
                                         {
                                             'message': translate(_('${name} should be an array of ntiids or empty.', mapping={'name': name}))
                                         },
                                         None)

        return set([x for x in result if x]) if result else None

    def _context_ntiids(self):
        return self._ntiids('context_ntiids')

    def _excluded_context_ntiids(self):
        return self._ntiids('excluded_context_ntiids')

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
