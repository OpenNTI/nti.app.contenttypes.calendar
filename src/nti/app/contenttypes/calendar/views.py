#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.view_mixins import BatchingUtilsMixin
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.appserver.ugd_edit_views import UGDPutView

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent

from nti.dataserver import authorization as nauth

@view_config(route_name='objects.generic.traversal',
             renderer="rest",
             request_method='POST',
             context=ICalendar,
             permission=nauth.ACT_CREATE)
class CalendarEventCreationView(AbstractAuthenticatedView,
                                ModeledContentUploadRequestUtilsMixin):

    def __call__(self):
        event = self.readCreateUpdateContentObject(self.remoteUser)
        self.context.store_event(event)
        self.request.response.status_int = 201
        return event


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarEvent,
             request_method='GET',
             permission=nauth.ACT_READ)
def get_calendar_event(event, request):
    return event


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarEvent,
             request_method='PUT',
             permission=nauth.ACT_UPDATE)
class CalendarEventUpdateView(UGDPutView):
    pass


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarEvent,
             request_method='DELETE',
             permission=nauth.ACT_DELETE)
class CalendarEventDeletionView(AbstractAuthenticatedView):

    def __call__(self):
        calendar = self.context.__parent__
        calendar.remove_event(self.context)
        self.request.response.status_int = 204
        return hexc.HTTPNoContent()


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendar,
             request_method='PUT',
             permission=nauth.ACT_UPDATE)
class CalendarUpdateView(UGDPutView):
    pass


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendar,
             request_method='GET',
             permission=nauth.ACT_READ)
class CalendarGetView(AbstractAuthenticatedView):

    def __call__(self):
        return self.context
