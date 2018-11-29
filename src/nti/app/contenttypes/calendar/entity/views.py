#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

from pyramid.view import view_config

from zope import component

from nti.app.contenttypes.calendar.views import CalendarContentsGetView

from nti.app.contenttypes.calendar.entity import CONTENTS_VIEW_NAME

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection

from nti.contenttypes.calendar.interfaces import ICalendarEventProvider

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IUser


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             context=ICalendarCollection,
             request_method='GET',
             permission=nauth.ACT_READ,
             name=CONTENTS_VIEW_NAME)
class UserCompositeCalendarView(CalendarContentsGetView):
    """
    Return all calendar events from user, community, groups and enrolled courses.
    """

    def get_source_items(self):
        items = []
        providers = component.subscribers((self.context.user,), ICalendarEventProvider)
        for x in providers or ():
            items.extend(x.iter_events())
        return items
