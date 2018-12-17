#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

import fudge

from hamcrest import has_length
from hamcrest import assert_that

from nti.app.contenttypes.calendar.entity.decorators import _MyCalendarLinkDecorator
from nti.app.contenttypes.calendar.entity.decorators import _UserCalendarLinkDecorator
from nti.app.contenttypes.calendar.entity.decorators import _CommunityCalendarLinkDecorator
from nti.app.contenttypes.calendar.entity.decorators import _FriendsListCalendarLinkDecorator

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.dataserver.tests import mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import Community
from nti.dataserver.users import FriendsList
from nti.dataserver.users import DynamicFriendsList

from nti.externalization.externalization import toExternalObject


class TestDecorators(ApplicationLayerTest):

    def _decorate(self, decorator, context):
        external = toExternalObject(context, decorate=False)
        decorator = decorator(context, None)
        decorator.decorateExternalMapping(context, external)
        return external

    @WithMockDSTrans
    @fudge.patch('nti.app.contenttypes.calendar.entity.decorators.has_permission')
    def test_my_calendar_link_decorator(self, mock_has_permission):
        mock_has_permission.is_callable().returns(True)
        user = self._create_user(u'test001')
        external = self._decorate(_MyCalendarLinkDecorator, user)
        links = [x.rel for x in external['Links'] if x.rel == 'contents']
        assert_that(links, has_length(1))

    @WithMockDSTrans
    @fudge.patch('nti.app.contenttypes.calendar.entity.decorators.has_permission')
    def test_user_calendar_link_decorator(self, mock_has_permission):
        mock_has_permission.is_callable().returns(True)
        user = self._create_user(u'test001')
        external = self._decorate(_UserCalendarLinkDecorator, user)
        links = [x.rel for x in external['Links'] if x.rel == 'Calendar']
        assert_that(links, has_length(1))

    @WithMockDSTrans
    @fudge.patch('nti.app.contenttypes.calendar.entity.decorators.has_permission')
    def test_community_calendar_link_decorator(self, mock_has_permission):
        mock_has_permission.is_callable().returns(True)
        community = Community.create_community(self.ds, username=u'test001')
        external = self._decorate(_CommunityCalendarLinkDecorator, community)
        links = [x.rel for x in external['Links'] if x.rel == 'Calendar']
        assert_that(links, has_length(1))

    @WithMockDSTrans
    def test_friendslist_calendar_link_decorator(self):
        obj = DynamicFriendsList(username=u'test001')
        mock_dataserver.current_transaction.add(obj)
        external = self._decorate(_FriendsListCalendarLinkDecorator, obj)
        links = [x.rel for x in external['Links'] if x.rel == 'Calendar']
        assert_that(links, has_length(1))

        obj = FriendsList(username=u'test002')
        mock_dataserver.current_transaction.add(obj)
        external = self._decorate(_FriendsListCalendarLinkDecorator, obj)
        links = [x.rel for x in external['Links'] if x.rel == 'Calendar']
        assert_that(links, has_length(0))
