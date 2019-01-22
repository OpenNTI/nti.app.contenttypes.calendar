#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

import fudge
import time

from datetime import datetime

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import not_none
from hamcrest import has_entries
from hamcrest import has_properties

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.contenttypes.calendar.interfaces import ICalendarEventURLProvider

from nti.contenttypes.calendar.model import CalendarEvent

from nti.dataserver.tests import mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans


class TestAdapters(ApplicationLayerTest):

    @fudge.patch('nti.app.contenttypes.calendar.utils.get_current_request')
    def test_calendar_event_url_provider(self, mock_request):
        class _MockRequest(object):
            def route_url(self, route_name, *elements, **kw):
                return '/dataserver2/'+'/'.join(elements)
            def resource_url(self, event):
                return u'/abc/efg'
        mock_request.is_callable().returns(_MockRequest())
        event = CalendarEvent(title=u'abc')
        provider = ICalendarEventURLProvider(event, None)
        assert_that(provider, not_none())
        assert_that(provider(), is_('/abc/efg'))

        event.ntiid = u'test_ntiid'
        assert_that(provider(), is_('/NextThoughtWebApp/id/test_ntiid'))

        mock_request.is_callable().returns(None)
        assert_that(provider(), is_(None))
