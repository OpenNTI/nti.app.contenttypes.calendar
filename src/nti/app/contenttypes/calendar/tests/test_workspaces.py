#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.appserver.workspaces import UserService

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.externalization.externalization import toExternalObject


class TestWorkspaces(ApplicationLayerTest):

    def require_collection_with_title(self, external, title):
        collections = [x for x in external['Items'] if x['Title'] == title]
        assert_that(collections, has_length(1))
        return collections[0]

    @WithMockDSTrans
    def test_workspaces(self):
        user = self._create_user('sjohnson@nextthought.com')
        service = UserService(user)
        workspace = [workspace for workspace in service.workspaces if workspace.name=='sjohnson@nextthought.com'][0]
        external = toExternalObject(workspace)

        result = self.require_collection_with_title(external, 'Calendars')
        link = self.require_link_href_with_rel(result, 'events')
        assert_that(link, is_('/dataserver2/users/sjohnson@nextthought.com/Calendars/@@events'))

        link = self.require_link_href_with_rel(result, 'export')
        assert_that(link, is_('/dataserver2/users/sjohnson@nextthought.com/Calendars/@@export'))
