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

from pyramid import httpexceptions as hexc

from pyramid.view import view_config

from requests.structures import CaseInsensitiveDict

from zope.cachedescriptors.property import Lazy

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.contenttypes.calendar import EXPORT_VIEW_NAME

from nti.app.externalization.error import raise_json_error

from nti.contenttypes.calendar.interfaces import ICalendar

from nti.dataserver import authorization as nauth


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendar,
             request_method='GET',
             permission=nauth.ACT_READ,
             name=EXPORT_VIEW_NAME)
class CalendarExportView(AbstractAuthenticatedView):

    def _transform_datetime(self, dt):
        return vDatetime(pytz.utc.localize(dt)) if dt is not None else None

    def _transform_timestamp(self, ts):
        if ts is not None:
            dt = datetime.datetime.utcfromtimestamp(ts)
            return self._transform_datetime(dt)
        return None

    def _build_ievent(self, source, dt_stamp):
        target = _iEvent()

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

        dt_stamp = self._transform_datetime(datetime.datetime.utcnow())
        for event in calendar.values():
            cal.add_component(self._build_ievent(event, dt_stamp=dt_stamp))

        return cal.to_ical()

    def _filename(self):
        # Maybe we should fallback title to be the username of user, title of course in the model?
        return self.context.title or 'calendar'

    def __call__(self):
        data = self._build_icalendar(self.context)

        response = self.request.response
        response.content_encoding = 'identity'
        response.content_type = 'text/ics; charset=UTF-8'
        response.content_disposition = 'attachment; filename="%s.ics"' % self._filename()

        stream = BytesIO()
        stream.write(data)

        stream.flush()
        stream.seek(0)
        response.body_file = stream
        return response
