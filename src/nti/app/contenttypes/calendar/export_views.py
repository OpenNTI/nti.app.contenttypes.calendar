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
import os
import pytz
import shutil
import tempfile

from icalendar import Calendar as _iCalendar
from icalendar import Event as _iEvent
from icalendar import vDatetime

from io import BytesIO

from pyramid.view import view_config

from pyramid import httpexceptions as hexc

from requests.structures import CaseInsensitiveDict

from zc.displayname.interfaces import IDisplayNameGenerator

from zope import component

from zope.cachedescriptors.property import Lazy

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.contenttypes.calendar import EXPORT_VIEW_NAME

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.base._compat import text_

from nti.cabinet.filer import DirectoryFiler

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


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendar,
             request_method='GET',
             permission=nauth.ACT_READ,
             name=EXPORT_VIEW_NAME)
class CalendarExportView(AbstractAuthenticatedView, CalendarExportMixin):

    def __call__(self):
        data = self._build_icalendar(self.context)

        response = self.request.response
        response.content_encoding = 'identity'
        response.content_type = 'text/ics; charset=UTF-8'
        response.content_disposition = 'attachment; filename="%s"' % self._filename(self.context)

        stream = BytesIO()
        stream.write(data)

        stream.flush()
        stream.seek(0)
        response.body_file = stream
        return response


class _CalendarExportFiler(DirectoryFiler):

    def __init__(self, zipname, path):
        self.zipname= zipname
        super(_CalendarExportFiler, self).__init__(path)

    def prepare(self, path=None):
        self.path = path if path else self.path
        if not self.path:
            self.path = tempfile.mkdtemp()
        else:
            self.path = super(_CalendarExportFiler, self).prepare(self.path)

    def asZip(self, path=None):
        base_name = path or tempfile.mkdtemp()
        base_name = os.path.join(base_name, self.zipname)
        if os.path.exists(base_name + ".zip"):
            os.remove(base_name + ".zip")
        result = shutil.make_archive(base_name, 'zip', self.path)
        return result


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarCollection,
             request_method='GET',
             permission=nauth.ACT_READ,
             name=EXPORT_VIEW_NAME)
class BulkCalendarExportView(AbstractAuthenticatedView, CalendarExportMixin):

    def __init__(self, request):
        super(BulkCalendarExportView, self).__init__(request)
        self._cache_filenames = set()

    def _zipname(self):
        return '%s_%s' % (self.remoteUser.username, u'calendars')

    def _filename(self, calendar, index=None):
        prefix = calendar.title or u'calendar'
        filename = "%s.ics" % prefix if index is None else "%s_%s.ics" % (prefix, index)
        return safe_filename(filename)

    def _generate_calendar_filename(self, calendar):
        filename = self._filename(calendar)
        index = 0
        while filename in self._cache_filenames:
            index = index + 1
            filename = self._filename(calendar, index)
        self._cache_filenames.add(filename)
        return filename

    def _export_calendars(self, path):
        zipname = self._zipname()
        filer = _CalendarExportFiler(zipname, path)
        try:
            filer.prepare()
            logger.info('Initiating calendars export')

            for calendar in self._calendars:
                source = self._build_icalendar(calendar)
                filer.save(self._generate_calendar_filename(calendar),
                           source,
                           bucket=text_(zipname),
                           contentType="text/ics",
                           overwrite=True)

            return filer.asZip(path=path)
        finally:
            filer.reset()

    @Lazy
    def _calendars(self):
        return self.context.container

    def __call__(self):
        # if no calendars, the download zip file can not be opened.
        if not self._calendars:
            return hexc.HTTPNoContent()

        path = tempfile.mkdtemp()
        try:
            zip_file = self._export_calendars(path)
            filename = os.path.split(zip_file)[1]

            response = self.request.response
            response.content_encoding = 'identity'
            response.content_type = 'application/zip; charset=UTF-8'
            content_disposition = 'attachment; filename="%s"' % filename
            response.content_disposition = str(content_disposition)
            response.body_file = open(zip_file, "rb")
            return response
        finally:
            shutil.rmtree(path, True)
