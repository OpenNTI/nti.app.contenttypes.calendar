#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

import fudge

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

from zope import component
from zope import interface

from nti.app.contenttypes.calendar.entity.decorators import _UserCalendarLinkDecorator
from nti.app.contenttypes.calendar.entity.decorators import _CommunityCalendarLinkDecorator

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import Community

from nti.externalization.externalization import toExternalObject


class TestDecorators(ApplicationLayerTest):

    def _decorate(self, decorator, context):
        external = toExternalObject(context, decorate=False)
        decorator = decorator(context, None)
        decorator.decorateExternalMapping(context, external)
        return external

    @WithMockDSTrans
    @fudge.patch('nti.app.contenttypes.calendar.entity.decorators.has_permission')
    def test_user_calendar_link_decorator(self, mock_has_permission):
        mock_has_permission.is_callable().returns(True)
        user = self._create_user(u'test001')
        external = self._decorate(_UserCalendarLinkDecorator, user)
        links = [x.rel for x in external['Links'] if x.rel == 'UserCalendar']
        assert_that(links, has_length(1))

    @WithMockDSTrans
    @fudge.patch('nti.app.contenttypes.calendar.entity.decorators.has_permission')
    def test_user_calendar_link_decorator(self, mock_has_permission):
        mock_has_permission.is_callable().returns(True)
        community = Community.create_community(self.ds, username=u'test001')
        external = self._decorate(_CommunityCalendarLinkDecorator, community)
        links = [x.rel for x in external['Links'] if x.rel == 'CommunityCalendar']
        assert_that(links, has_length(1))
