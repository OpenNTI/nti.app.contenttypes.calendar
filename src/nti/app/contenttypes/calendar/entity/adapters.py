#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid.interfaces import IRequest

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation.interfaces import IAnnotations

from zope.traversing.interfaces import IPathAdapter

from nti.app.contenttypes.calendar.entity.model import IUserCalendar

from nti.app.contenttypes.calendar.entity.model import UserCalendar

from nti.dataserver.interfaces import IUser

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUser)
@interface.implementer(IUserCalendar)
def _UserCalendarFactory(user, create=True):
    result = None
    KEY = u'UserCalendar'
    annotations = IAnnotations(user)
    try:
        result = annotations[KEY]
    except KeyError:
        if create:
            result = UserCalendar()
            annotations[KEY] = result
            result.__name__ = KEY
            result.__parent__ = user
            connection = IConnection(user, None)
            if connection is not None:
                # pylint: disable=too-many-function-args
                connection.add(result)
    return result


@interface.implementer(IPathAdapter)
@component.adapter(IUser, IRequest)
def _UserCalendarPathAdapter(context, request):
    return _UserCalendarFactory(context)
