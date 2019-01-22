#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

from datetime import datetime

from zope import component

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from requests.structures import CaseInsensitiveDict

from zope.cachedescriptors.property import Lazy

from nti.app.base.abstract_views import AbstractAuthenticatedView
from nti.app.base.abstract_views import get_all_sources
from nti.app.base.abstract_views import get_safe_source_filename

from nti.app.contentfile import validate_sources

from nti.app.contentfolder.resources import is_internal_file_link

from nti.app.contenttypes.calendar import GENERATE_FEED_URL
from nti.app.contenttypes.calendar import CONTENTS_VIEW_NAME

from nti.app.contenttypes.calendar import MessageFactory as _

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.app.contenttypes.calendar.utils import generate_ics_feed_url

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import BatchingUtilsMixin
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.appserver.ugd_edit_views import UGDPutView

from nti.common.string import is_true

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarEvent
from nti.contenttypes.calendar.interfaces import ICalendarDynamicEventProvider

from nti.dataserver import authorization as nauth

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.externalization import to_external_object

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL


class MultiPartHandleMixin(object):

    _iface_provided = ICalendarEvent

    @Lazy
    def filer(self):
        return None

    def _handle_multipart(self, contentObject, sources):
        if self.filer is None:
            return

        for name, source in sources.items():
            if name in self._iface_provided:
                # remove existing
                location = getattr(contentObject, name, None)
                if location and is_internal_file_link(location):
                    self.filer.remove(location)

                # save a in a new file
                key = get_safe_source_filename(source, name)
                location = self.filer.save(key, source,
                                           overwrite=False,
                                           structure=True,
                                           context=contentObject)
                setattr(contentObject, name, location)


@view_config(route_name='objects.generic.traversal',
             renderer="rest",
             request_method='POST',
             context=ICalendar,
             permission=nauth.ACT_CREATE)
class CalendarEventCreationView(AbstractAuthenticatedView,
                                ModeledContentUploadRequestUtilsMixin,
                                MultiPartHandleMixin):

    def _transform(self, contentObject):
        return contentObject

    def __call__(self):
        contentObject = self.readCreateUpdateContentObject(self.remoteUser)
        contentObject = self._transform(contentObject)
        self.context.store_event(contentObject)

        # multi-part data
        sources = get_all_sources(self.request)
        if sources:
            validate_sources(self.remoteUser, contentObject, sources)
            self._handle_multipart(contentObject, sources)

        self.request.response.status_int = 201
        return contentObject


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
class CalendarEventUpdateView(UGDPutView, MultiPartHandleMixin):

    def __call__(self):
        contentObject = super(CalendarEventUpdateView, self).__call__()

        # multi-part data
        sources = get_all_sources(self.request)
        if sources:
            validate_sources(self.remoteUser, contentObject, sources)
            self._handle_multipart(contentObject, sources)

        return contentObject


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
def get_calendar(context, request):
    return context


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendar,
             request_method='GET',
             permission=nauth.ACT_READ,
             name=CONTENTS_VIEW_NAME)
class CalendarContentsGetView(AbstractAuthenticatedView, BatchingUtilsMixin):

    _DEFAULT_BATCH_SIZE = 50
    _DEFAULT_BATCH_START = 0

    _allowed_sorting_fields = {'title': lambda x: x.title.lower(),
                               'description': lambda x: x.description and x.description.lower(),
                               'location': lambda x: x.location and x.location.lower(),
                               'start_time': lambda x: x.start_time,
                               'end_time': lambda x: (x.end_time is not None, x.end_time),
                               'createdtime': lambda x: x.createdTime,
                               'lastModified': lambda x: x.lastModified}

    _allowed_sorting_orders = ('ascending', 'descending')

    @Lazy
    def _params(self):
        return CaseInsensitiveDict(self.request.params)

    def _time_param(self, pname):
        timestamp = self._params.get(pname)
        timestamp = float(timestamp) if timestamp is not None else None
        return datetime.utcfromtimestamp(timestamp) if timestamp else None

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
            # All events not yet completed before this timestamp.
            res['notBefore'] = lambda x: (x.start_time is not None and x.start_time >= notBefore) \
                                      or (x.end_time is not None and x.end_time >= notBefore)
        if notAfter:
            # All events started before this timestamp (may or may not be complete)
            res['notAfter'] = lambda x: (x.start_time is not None and x.start_time <= notAfter)
        if mimeType:
            res['mimeType'] = lambda x: x.mimeType == mimeType

        return res

    def get_source_items(self):
        events = [x for x in self.context.values()]

        exclude_dynamic = is_true(self._params.get('exclude_dynamic_events'))
        if not exclude_dynamic:
            # May have other better way to get the course.
            providers = component.subscribers((self.remoteUser, self.context.__parent__),
                                              ICalendarDynamicEventProvider)
            for x in providers or ():
                events.extend(x.iter_events())
        return events

    def _filter_items(self, filters, items=None):
        items = self.get_source_items() if items is None else items
        if not filters:
            return items

        def _include_item(item):
            for _filter in filters.values():
                if not _filter(item):
                    return False
            return True

        return [x for x in items if _include_item(x)]

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
        try:
            filters = self._filter_params()
            sortOn, sortOrder = self._sort_params()

            total_items = self.get_source_items()
            items = self._filter_items(filters, items=total_items)
            items = self._sorted_items(items, sortOn, sortOrder)

            result = LocatedExternalDict()
            result.__name__ = self.request.view_name
            result.__parent__ = self.request.context
            result[TOTAL] = len(total_items)

            if filters:
                result['FilteredTotalItemCount'] = len(items)

            self._batch_items_iterable(result,
                                       items,
                                       number_items_needed=len(items))
            return result
        except ValueError as e:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': str(e),
                             },
                             None)


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarCollection,
             permission=nauth.ACT_READ,
             request_method='GET')
class CalendarCollectionView(AbstractAuthenticatedView,
                             BatchingUtilsMixin):
    """
    A generic :class:`ICalendarCollection` view that supports paging on the
    collection.
    """

    #: To maintain BWC; disable paging by default.
    _DEFAULT_BATCH_SIZE = None
    _DEFAULT_BATCH_START = None

    def __call__(self):
        result = to_external_object(self.context)
        result[TOTAL] = len(result[ITEMS])
        self._batch_items_iterable(result,
                                   result[ITEMS],
                                   number_items_needed=result[TOTAL])
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarCollection,
             permission=nauth.ACT_READ,
             name=GENERATE_FEED_URL,
             request_method='GET')
class GenerateCalendarFeedURL(AbstractAuthenticatedView):
    """
    Generates and returns a calendar feed url.
    """

    def __call__(self):
        return generate_ics_feed_url(self.context.user, self.request)
