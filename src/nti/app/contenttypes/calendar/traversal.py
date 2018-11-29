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

from nti.app.contenttypes.calendar.workspaces import CalendarCollection


@interface.implementer(IPathAdapter)
@component.adapter(IUser)
def calendar_collection_path_adapter(user, request):
    return CalendarCollection(user)
