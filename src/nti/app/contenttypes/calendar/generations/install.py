#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.intid.interfaces import IIntIds

from zope.generations.generations import SchemaManager

from nti.contenttypes.calendar.index import install_calendar_event_catalog

generation = 1

logger = __import__('logging').getLogger(__name__)


class _CalendarSchemaManager(SchemaManager):

    def __init__(self):
        super(_CalendarSchemaManager, self).__init__(generation=generation,
                                                     minimum_generation=generation,
                                                     package_name='nti.app.contenttypes.calendar.generations')


def evolve(context):
    conn = context.connection
    root = conn.root()
    dataserver_folder = root['nti.dataserver']

    lsm = dataserver_folder.getSiteManager()
    intids = lsm.getUtility(IIntIds)
    install_calendar_event_catalog(dataserver_folder, intids)
