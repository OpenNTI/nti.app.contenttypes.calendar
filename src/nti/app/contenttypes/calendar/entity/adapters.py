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

from nti.app.contenttypes.calendar.entity.interfaces import IUserCalendar
from nti.app.contenttypes.calendar.entity.interfaces import ICommunityCalendar

from nti.app.contenttypes.calendar.entity.model import UserCalendar
from nti.app.contenttypes.calendar.entity.model import CommunityCalendar

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import ICommunity

logger = __import__('logging').getLogger(__name__)


def _create_annotation(parent, key, calendar_factory, create=True):
    result = None
    annotations = IAnnotations(parent)
    try:
        result = annotations[key]
    except KeyError:
        if create:
            result = calendar_factory()
            annotations[key] = result
            result.__name__ = key
            result.__parent__ = parent
            connection = IConnection(parent, None)
            if connection is not None:
                # pylint: disable=too-many-function-args
                connection.add(result)
    return result


@component.adapter(IUser)
@interface.implementer(IUserCalendar)
def _UserCalendarFactory(user, create=True):
    return _create_annotation(user, u'UserCalendar', UserCalendar, create=create)


@interface.implementer(IPathAdapter)
@component.adapter(IUser, IRequest)
def _UserCalendarPathAdapter(context, request):
    return _UserCalendarFactory(context)


@component.adapter(ICommunity)
@interface.implementer(ICommunityCalendar)
def _CommunityCalendarFactory(community, create=True):
    return _create_annotation(community, u'CommunityCalendar', CommunityCalendar, create=create)


@interface.implementer(IPathAdapter)
@component.adapter(ICommunity, IRequest)
def _CommunityCalendarPathAdapter(context, request):
    return _CommunityCalendarFactory(context)
