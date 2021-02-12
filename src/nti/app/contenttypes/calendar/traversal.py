#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from zope.traversing.interfaces import IPathAdapter

from nti.dataserver.interfaces import IUser

from nti.app.contenttypes.calendar.interfaces import ICalendarCollection
from nti.app.contenttypes.calendar.interfaces import IAdminCalendarCollection

from nti.appserver.workspaces.interfaces import IUserService


@component.adapter(IUser)
@interface.implementer(IPathAdapter)
def calendar_collection_path_adapter(user, unused_request):
    service = IUserService(user)
    return ICalendarCollection(service.user_workspace, None)


@component.adapter(IUser)
@interface.implementer(IPathAdapter)
def admin_calendar_collection_path_adapter(user, unused_request):
    service = IUserService(user)
    return IAdminCalendarCollection(service.user_workspace, None)
