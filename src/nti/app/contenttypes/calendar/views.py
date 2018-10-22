#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

import datetime

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from requests.structures import CaseInsensitiveDict

from zope.cachedescriptors.property import Lazy

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import BatchingUtilsMixin
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.appserver.ugd_edit_views import UGDPutView

from nti.common.string import is_true

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent

from nti.dataserver import authorization as nauth

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields


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
class CalendarGetView(AbstractAuthenticatedView, BatchingUtilsMixin):

    _allowed_sorting_fields = {'title': lambda x: x.title,
                               'description': lambda x: x.description,
                               'location': lambda x: x.location,
                               'start_time': lambda x: x.start_time,
                               'end_time': lambda x: x.end_time,
                               'createdtime': lambda x: x.createdTime,
                               'lastModified': lambda x: x.lastModified}

    _allowed_sorting_orders = ('ascending', 'descending')

    @Lazy
    def _params(self):
        return CaseInsensitiveDict(self.request.params)

    def _time_param(self, pname):
        timestamp = self._params.get(pname)
        timestamp = float(timestamp) if timestamp is not None else None
        return datetime.datetime.utcfromtimestamp(timestamp) if timestamp else None

    def _str_param(self, pname):
        val = self._params.get(pname)
        val = val.strip() if val else None
        return val.lower() if val else None

    def _filter_params(self):
        mimeType = self._str_param('mimeType')
        notBefore = self._time_param('notBefore')
        notAfter = self._time_param('notAfter')

        if notBefore and notAfter and notBefore > notAfter:
            raise ValueError(u"notBefore should be less than notAfter")

        res = {}
        if notBefore:
            res['notBefore'] = lambda x: x.end_time is None or x.end_time >= notBefore
        if notAfter:
            res['notAfter'] = lambda x: x.start_time is None or x.start_time <= notAfter
        if mimeType:
            res['mimeType'] = lambda x: x.mimeType == mimeType

        return res

    def _filter_items(self, filters):
        if not filters:
            return [x for x in self.context.values()]

        def _include_item(item):
            for _filter in filters.values():
                if not _filter(item):
                    return False
            return True

        return [x for x in self.context.values() if _include_item(x)]

    def _sort_params(self):
        sortOn = self._params.get('sortOn')
        sortOrder = self._params.get('sortOrder')

        if sortOn is not None and sortOn not in self._allowed_sorting_fields:
            raise ValueError(u"Invalid value for 'sortOn'")

        if sortOrder is not None and sortOrder not in self._allowed_sorting_orders:
            raise ValueError(u"Invalid value for 'sortOrder'")

        return sortOn, sortOrder == 'descending'

    def _sorted_items(self, items, sortOn=None, sortOrder=None):
        return items if sortOn is None or sortOrder is None else sorted(items,
                                                                        key=self._allowed_sorting_fields.get(sortOn),
                                                                        reverse=sortOrder)

    def __call__(self):
        raw = is_true(self._params.get('raw'))
        if raw:
            return self.context

        try:
            filters = self._filter_params()
            sortOn, sortOrder = self._sort_params()

            items = self._filter_items(filters)
            items = self._sorted_items(items, sortOn, sortOrder)

            result = LocatedExternalDict()
            result.__name__ = self.request.view_name
            result.__parent__ = self.request.context
            result[StandardExternalFields.TOTAL] = len(items)
            self._batch_items_iterable(result,
                                       items,
                                       number_items_needed=result[StandardExternalFields.TOTAL])
            return result
        except ValueError as e:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': str(e),
                             },
                             None)
