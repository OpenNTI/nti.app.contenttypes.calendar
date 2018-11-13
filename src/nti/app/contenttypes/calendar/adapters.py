#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

logger = __import__('logging').getLogger(__name__)

from zope import component
from zope import interface

from nti.contenttypes.calendar.interfaces import ICalendarEvent

from nti.site.interfaces import IHostPolicyFolder

from nti.traversal.traversal import find_interface

@component.adapter(ICalendarEvent)
@interface.implementer(IHostPolicyFolder)
def _calendar_event_to_policy_folder(context):
    return find_interface(context, IHostPolicyFolder, strict=False)
