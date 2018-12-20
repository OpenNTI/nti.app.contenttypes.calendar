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
import pytz

from icalendar import Calendar as _iCalendar
from icalendar import Event as _iEvent
from icalendar import vDatetime

from io import BytesIO

from pyramid.view import view_config
from pyramid.view import view_defaults

from requests.structures import CaseInsensitiveDict

from zc.displayname.interfaces import IDisplayNameGenerator

from zope import component

from zope.cachedescriptors.property import Lazy

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.contenttypes.calendar import EXPORT_VIEW_NAME

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.common.string import is_true

from nti.contenttypes.calendar.interfaces import ICalendar
from nti.contenttypes.calendar.interfaces import ICalendarDynamicEventProvider

from nti.dataserver import authorization as nauth

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.namedfile.file import safe_filename


def _mime_type(obj):
    return getattr(obj, 'mimeType', None) or getattr(obj, 'mime_type', None)

class CalendarExportMixin(object):

    @Lazy
    def _params(self):
        return CaseInsensitiveDict(self.request.params)

    def _transform_datetime(self, dt):
        return vDatetime(pytz.utc.localize(dt)) if dt is not None else None

    def _transform_timestamp(self, ts):
        if ts is not None:
            dt = datetime.datetime.utcfromtimestamp(ts)
            return self._transform_datetime(dt)
        return None

    def _build_ievent(self, source, dt_stamp):
        target = _iEvent()
        target['X-NTIID'] = source.ntiid or u''
        target['X-NTI-MIMETYPE'] = _mime_type(source) or u''

        # dtstamp represents when this event is added into the ics file.
        target['dtstamp'] = dt_stamp

        # add text fields.
        for target_attr, source_attr in (('Summary', 'title'),
                                         ('Description', 'description'),
                                         ('Location', 'location')):
            target[target_attr] = getattr(source, source_attr) or ''

        # add date fields, date value can not be empty string in Google calendar.
        for target_attr, source_attr, _trans in (('created', 'createdTime', self._transform_timestamp),
                                                 ('last-modified', 'lastModified', self._transform_timestamp),
                                                 ('dtstart', 'start_time', self._transform_datetime),
                                                 ('dtend', 'end_time', self._transform_datetime)):
            val = _trans(getattr(source, source_attr))
            if val is not None:
                target[target_attr] = val

        return target

    def _build_icalendar(self, calendar):
        cal = _iCalendar()
        cal['title'] = calendar.title
        cal['description'] = calendar.description or u''
        cal['X-NTIID'] = calendar.ntiid or u''
        cal['X-NTI-MIMETYPE'] = _mime_type(calendar) or u''

        dt_stamp = self._transform_datetime(datetime.datetime.utcnow())

        for event in self._events_for_calendar(calendar):
            cal.add_component(self._build_ievent(event, dt_stamp=dt_stamp))

        return cal.to_ical()

    def _events_for_calendar(self, calendar):
        events = [x for x in calendar.values()]

        # It won't show any dynamic events by default.
        exclude_dynamic = is_true(self._params.get('exclude_dynamic_events'))
        if not exclude_dynamic:
            providers = component.subscribers((self.remoteUser, calendar.__parent__),
                                              ICalendarDynamicEventProvider)
            for x in providers or ():
                events.extend(x.iter_events())

        return events

    def _display_name(self, user, request):
        name = IFriendlyNamed(user).realname
        if not name:
            name = component.getMultiAdapter((user, request),
                                             IDisplayNameGenerator)()
        return name

    def _filename(self, calendar):
        displayname = self._display_name(self.remoteUser,
                                         self.request)
        filename = '%s_%s.ics' % (displayname, calendar.title or u'calendar')
        return safe_filename(filename)

    def _make_response(self, data, filename):
        response = self.request.response
        response.content_encoding = 'identity'
        response.content_type = 'text/calendar; charset=UTF-8'
        response.content_disposition = 'attachment; filename="%s"' % filename

        stream = BytesIO()
        stream.write(data)

        stream.flush()
        stream.seek(0)
        response.body_file = stream
        return response


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendar,
             request_method='GET',
             permission=nauth.ACT_READ,
             name=EXPORT_VIEW_NAME)
class CalendarExportView(AbstractAuthenticatedView, CalendarExportMixin):

    def __call__(self):
        data = self._build_icalendar(self.context)
        filename = self._filename(self.context)
        return self._make_response(data, filename)


@view_config(request_method='GET')
@view_config(request_method='POST')
@view_defaults(route_name='objects.generic.traversal',
               renderer='rest',
               context=ICalendarCollection,
               permission=nauth.ACT_READ,
               name=EXPORT_VIEW_NAME)
class BulkCalendarExportView(AbstractAuthenticatedView, CalendarExportMixin):

    def _filename(self):
        displayname = self._display_name(self.remoteUser,
                                         self.request)
        filename = '%s_%s.ics' % (displayname, u'calendars')
        return safe_filename(filename)

    @Lazy
    def _calendars(self):
        return self.context.container

    def _build_icalendar(self):
        cal = _iCalendar()
        cal['title'] = u'My Calendars'

        dt_stamp = self._transform_datetime(datetime.datetime.utcnow())
        for x in self._calendars:
            for event in self._events_for_calendar(x):
                cal.add_component(self._build_ievent(event, dt_stamp=dt_stamp))

        return cal.to_ical()

    def __call__(self):
        try:
            data = self._build_icalendar()
            filename = self._filename()
            return self._make_response(data, filename)
        finally:
            self.request.environ['nti.commit_veto'] = 'abort'


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarCollection,
             request_method='GET',
             permission=nauth.ACT_READ,
             name='calendar_feed.ics')
class CalendarContentsFeedView(BulkCalendarExportView):
    pass

