#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from zope import component

from zope.i18n import translate

from zope.cachedescriptors.property import Lazy

from nti.app.contenttypes.calendar import MessageFactory as _

from nti.app.contenttypes.calendar.views import CalendarContentsGetView

from nti.app.contenttypes.calendar.entity import EVENTS_VIEW_NAME

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.app.externalization.error import raise_json_error

from nti.common.string import is_true

from nti.contenttypes.calendar.interfaces import ICalendarEventProvider

from nti.dataserver import authorization as nauth

logger = __import__('logging').getLogger(__name__)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarCollection,
             request_method='GET',
             permission=nauth.ACT_READ,
             name=EVENTS_VIEW_NAME)
class UserCompositeCalendarView(CalendarContentsGetView):
    """
    Return all calendar events from user, community, groups and enrolled courses.
    """

    def _context_ntiids(self):
        result = self.request.params.getall('context_ntiids')
        return [x for x in result or () if x]

    def _excluded_context_ntiids(self):
        result = self.request.params.getall('excluded_context_ntiids')
        return [x for x in result or () if x]

    def get_source_items(self):
        items = []
        context_ntiids = self._context_ntiids()
        excluded_context_ntiids = self._excluded_context_ntiids()
        exclude_dynamic = is_true(self._params.get('exclude_dynamic_events'))

        providers = component.subscribers((self.context.user,),
                                          ICalendarEventProvider)
        for x in providers or ():
            items.extend(x.iter_events(context_ntiids=context_ntiids,
                                       excluded_context_ntiids=excluded_context_ntiids,
                                       exclude_dynamic=exclude_dynamic))
        return items


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarCollection,
             request_method='GET',
             permission=nauth.ACT_READ,
             name='calendar_feed.ics')
class CalendarContentsFeedView(UserCompositeCalendarView):

    _DEFAULT_BATCH_SIZE = None
    _DEFAULT_BATCH_START = None


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarCollection,
             request_method='POST',
             permission=nauth.ACT_READ,
             name=EVENTS_VIEW_NAME)
class UserCompositeCalendarDoomPostView(UserCompositeCalendarView):
    """
    Use this Post view for long uri request.
    """
    @Lazy
    def _body(self):
        try:
            return self.request.json_body
        except ValueError as e:
            logger.debug("Ignoring bad body: %s", str(e))
            return {}

    def _ntiids(self, name):
        ntiids = self._body.get(name)
        if ntiids is not None and not isinstance(ntiids, list):
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': translate(_('${name} should be an array of ntiids or empty.', mapping={'name': name}))
                             },
                             None)
        return set(ntiids) if ntiids else None

    def _context_ntiids(self):
        return self._ntiids('context_ntiids')

    def _excluded_context_ntiids(self):
        return self._ntiids('excluded_context_ntiids')

    def __call__(self):
        try:
            result = super(UserCompositeCalendarDoomPostView, self).__call__()
            return result
        finally:
            self.request.environ['nti.commit_veto'] = 'abort'
            logger.debug("Always dooming the transaction for UserCompositeCalendarDoomPostView.")
