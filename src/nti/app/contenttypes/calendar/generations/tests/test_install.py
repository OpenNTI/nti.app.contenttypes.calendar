#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import has_key
from hamcrest import not_none
from hamcrest import assert_that

import unittest

from nti.app.contenttypes.calendar.tests import SharedConfiguringTestLayer

from nti.contenttypes.calendar.index import get_calendar_event_catalog

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans


class TestInstall(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    @WithMockDSTrans
    def test_installed(self):
        conn = mock_dataserver.current_transaction
        root = conn.root()
        generations = root['zope.generations']
        assert_that(generations, has_key('nti.dataserver-app-calendar'))

        catalog = get_calendar_event_catalog()
        assert_that(catalog, not_none())
