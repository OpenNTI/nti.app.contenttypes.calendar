#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import nameparser

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

from nti.app.contenttypes.calendar.interfaces import DuplicateAttendeeError
from nti.app.contenttypes.calendar.interfaces import IAdminCalendarCollection
from nti.app.contenttypes.calendar.interfaces import ICalendarCollection
from nti.app.contenttypes.calendar.interfaces import ICalendarEventAttendanceManager
from nti.app.contenttypes.calendar.interfaces import InvalidAttendeeError

from nti.app.products.courseware.interfaces import ACT_RECORD_EVENT_ATTENDANCE
from nti.app.products.courseware.interfaces import ACT_VIEW_EVENT_ATTENDANCE

from nti.contenttypes.calendar.interfaces import ICalendarEventAttendanceContainer
from nti.contenttypes.calendar.interfaces import IUserCalendarEventAttendance

from nti.dataserver.users import User

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.externalization.datetime import datetime_from_string

logger = __import__('logging').getLogger(__name__)

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

CLASS = StandardExternalFields.CLASS
ITEMS = StandardExternalFields.ITEMS
MIMETYPE = StandardExternalFields.MIMETYPE
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
        result = LocatedExternalDict()
        result.__name__ = self.request.view_name
        result.__parent__ = self.request.context
        calendars = sorted(self.context.iter_calendars(), key=lambda x: x.title.lower())
        self._batch_items_iterable(result, calendars)
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IAdminCalendarCollection,
             permission=nauth.ACT_READ,
             request_method='GET')
class AdminCalendarCollectionView(CalendarCollectionView):
    """
    A generic :class:`IAdminCalendarCollection` view that supports paging on the
    collection.
    """
    _DEFAULT_BATCH_SIZE = 20
    _DEFAULT_BATCH_START = 0


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


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarEventAttendanceContainer,
             permission=ACT_RECORD_EVENT_ATTENDANCE,
             request_method='POST')
class RecordCalendarEventAttendanceView(AbstractAuthenticatedView,
                                        ModeledContentUploadRequestUtilsMixin):
    """
    Post attendance for a given user to an event
    """

    def _get_user(self, values):
        username = values.get('Username') \
                   or values.get('user') \
                   or values.get('username')
        result = User.get_user(username)

        if result is None:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u"User not found."),
                                 'code': 'UserNotFound',
                             },
                             None)

        return result

    def _get_registration_time(self, values):
        registration_time = values.get('registrationTime')

        if registration_time is not None:
            registration_time = datetime_from_string(registration_time)

        return registration_time

    def __call__(self):
        values = self.readInput()
        user = self._get_user(values)
        registration_time = self._get_registration_time(values)

        try:
            event_manager = ICalendarEventAttendanceManager(self.context)
            attendance = event_manager.add_attendee(user,
                                                    creator=self.remoteUser.username,
                                                    registration_time=registration_time)
        except DuplicateAttendeeError as e:
            raise_json_error(self.request,
                             hexc.HTTPConflict,
                             {
                                 'message': _(u"Attendance already marked for user"),
                                 'code': 'DuplicateEntry'
                             },
                             None)
        except InvalidAttendeeError as e:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(str(e)),
                                 'code': 'InvalidAttendee',
                             },
                             None)

        event = ICalendarEvent(self.context)
        event_ntiid = getattr(event, 'ntiid', None)

        logger.info("'%s' marked attendance at event '%s' for user '%s'",
                    self.getRemoteUser(),
                    event_ntiid,
                    user.username)

        self.request.response.status_int = 201
        return attendance


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IUserCalendarEventAttendance,
             request_method='DELETE',
             permission=ACT_RECORD_EVENT_ATTENDANCE)
class CalendarEventAttendanceDeletionView(AbstractAuthenticatedView):

    def __call__(self):
        attendance_container = ICalendarEventAttendanceContainer(self.context)
        attendance_container.remove_attendance(self.context.__name__)
        self.request.response.status_int = 204
        return hexc.HTTPNoContent()


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IUserCalendarEventAttendance,
             request_method='GET',
             permission=ACT_VIEW_EVENT_ATTENDANCE)
class UserCalendarEventAttendanceView(AbstractAuthenticatedView):

    def __call__(self):
        return self.context


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=IUserCalendarEventAttendance,
             request_method='PUT',
             permission=ACT_RECORD_EVENT_ATTENDANCE)
class UserCalendarEventAttendanceView(UGDPutView):
    pass


class AttendanceSummary(object):

    def __init__(self, attendance, user):
        self.attendance = attendance
        self.user = user

    @Lazy
    def registrationTime(self):
        return self.attendance.registrationTime

    @Lazy
    def creator(self):
        return self.attendance.creator

    @Lazy
    def username(self):
        return getattr(self.user, 'username', '')

    @Lazy
    def alias(self):
        return getattr(IFriendlyNamed(self.user, None), 'alias', '')

    @Lazy
    def realname(self):
        return getattr(IFriendlyNamed(self.user, None), 'realname', '')

    @Lazy
    def last_name(self):
        lastname = u''
        realname = self.realname
        if realname and '@' not in realname and realname != self.username:
            human_name = nameparser.HumanName(realname)
            lastname = human_name.last or u''
        return lastname


@view_config(route_name='objects.generic.traversal',
             permission=ACT_VIEW_EVENT_ATTENDANCE,
             renderer='rest',
             context=ICalendarEventAttendanceContainer,
             request_method='GET')
class CalendarEventAttendanceView(AbstractAuthenticatedView,
                                  BatchingUtilsMixin):
    """
    Return the attendance for the calendar event.

    batchSize
            The size of the batch.  Defaults to 50.

    batchStart
            The starting batch index.  Defaults to 0.

    sortOn
            The case insensitive field to sort on. Options are ``lastname``,
            ``alias``, ``registrationTime``, ``creator``, ``username``.
            The default is by registrationTime.

    sortOrder
            The sort direction. Options are ``ascending`` and
            ``descending``. Sort order is ascending by default.

    """

    _DEFAULT_BATCH_SIZE = 50
    _DEFAULT_BATCH_START = 0

    _default_sort = 'registrationtime'
    _sort_keys = {
        'registrationtime': lambda x: x.registrationTime,
        'username': lambda x: x.username,
        'alias': lambda x: x.alias,
        'realname': lambda x: x.realname,
        'lastname': lambda x: x.last_name,
        'creator': lambda x: x.creator,
    }

    def _get_sorted_result_set(self, summaries, sort_key, sort_desc=False):
        """
        Get the sorted result set.
        """
        summaries = sorted(summaries, key=sort_key, reverse=sort_desc)
        return summaries

    def _get_sort_params(self):
        sort_on = self.request.params.get('sortOn') or ''
        sort_on = sort_on.lower()
        sort_on = sort_on if sort_on in self._sort_keys else self._default_sort
        sort_key = self._sort_keys.get(sort_on)

        # Ascending is default
        sort_order = self.request.params.get('sortOrder')
        sort_descending = bool(
            sort_order and sort_order.lower() == 'descending')

        return sort_key, sort_descending

    def _search_summaries(self, search_param, user_summaries):
        """
        For the given search_param, return the results for those users
        if it matches realname, alias, or displayable username.
        """
        # TODO: Possibly use the entity catalog

        def matches(summary):
            result = (
                    (summary.alias
                     and search_param in summary.alias.lower())
                    or (summary.username
                        and search_param in summary.username.lower())
                    or (summary.last_name
                        and search_param in summary.realname.lower())
            )
            return result

        results = [x for x in user_summaries if matches(x)]
        return results

    def _get_items(self, result_dict):
        """
        Sort and batch records.
        """
        attendance_container = self.context

        # Now build our data for each user
        summaries = []
        for username, attendance in attendance_container.items():
            summary = AttendanceSummary(attendance, User.get_user(username))
            summaries.append(summary)

        search = self.request.params.get('search')
        search_param = search and search.lower()

        if search_param:
            summaries = self._search_summaries(search_param, summaries)

        sort_key, sort_descending = self._get_sort_params()

        result_set = self._get_sorted_result_set(summaries,
                                                 sort_key,
                                                 sort_descending)

        def to_external(summary):
            return summary.attendance

        self._batch_items_iterable(result_dict,
                                   result_set,
                                   selector=to_external)

        return result_dict.get(ITEMS)

    def __call__(self):
        result_dict = LocatedExternalDict()

        result_dict[MIMETYPE] = 'application/vnd.nextthought.calendar.calendareventattendance'
        result_dict[CLASS] = 'CalendarEventAttendance'
        result_dict[ITEMS] = self._get_items(result_dict)

        return result_dict
