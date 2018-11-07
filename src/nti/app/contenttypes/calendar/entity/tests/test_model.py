#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

import datetime
import unittest

from hamcrest import assert_that
from hamcrest import contains
from hamcrest import has_entries
from hamcrest import has_length
from hamcrest import has_properties
from hamcrest import is_
from hamcrest import instance_of
from hamcrest import not_none
from hamcrest import same_instance
from hamcrest import starts_with

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.contenttypes.calendar.entity.model import UserCalendar
from nti.app.contenttypes.calendar.entity.model import UserCalendarEvent
from nti.app.contenttypes.calendar.entity.model import CommunityCalendar
from nti.app.contenttypes.calendar.entity.model import CommunityCalendarEvent

from nti.externalization import internalization

from nti.externalization.externalization import toExternalObject


class TestExternalization(ApplicationLayerTest):

    def _internalize(self, external, context=None, factory_=not_none()):
        factory = internalization.find_factory_for(external)
        assert_that(factory, is_(factory_))
        new_io = context if context is not None else (factory() if factory else None)
        if new_io is not None:
            internalization.update_from_external_object(new_io, external)
        return new_io

    def testUserCalendarEvent(self):
        now = datetime.datetime.utcnow()
        obj =  UserCalendarEvent(title=u'reading',
                             description=u'this is',
                             location=u'oklahoma',
                             end_time=now,
                             icon=u'/abc/efg')
        assert_that(obj.start_time, is_(obj.created))

        external = toExternalObject(obj)
        assert_that(external, has_entries({'Class': 'UserCalendarEvent',
                                           'title': 'reading',
                                           'description': 'this is',
                                           'location': 'oklahoma',
                                           'start_time': not_none(),
                                           'end_time': not_none(),
                                           'icon': '/abc/efg',
                                           'Last Modified': not_none(),
                                           'MimeType': 'application/vnd.nextthought.calendar.usercalendarevent'}))

        new_io = self._internalize(external)
        assert_that(new_io, instance_of(UserCalendarEvent))
        assert_that(new_io, has_properties({'title': 'reading',
                                            'description': 'this is',
                                            'location': 'oklahoma',
                                            'start_time': not_none(),
                                            'end_time': not_none(),
                                            'icon': '/abc/efg',
                                            'lastModified': not_none()}))

    def testCommunityCalendarEvent(self):
        now = datetime.datetime.utcnow()
        obj =  CommunityCalendarEvent(title=u'reading',
                             description=u'this is',
                             location=u'oklahoma',
                             end_time=now,
                             icon=u'/abc/efg')
        assert_that(obj.start_time, is_(obj.created))

        external = toExternalObject(obj)
        assert_that(external, has_entries({'Class': 'CommunityCalendarEvent',
                                           'title': 'reading',
                                           'description': 'this is',
                                           'location': 'oklahoma',
                                           'start_time': not_none(),
                                           'end_time': not_none(),
                                           'icon': '/abc/efg',
                                           'Last Modified': not_none(),
                                           'MimeType': 'application/vnd.nextthought.calendar.communitycalendarevent'}))

        new_io = self._internalize(external)
        assert_that(new_io, instance_of(CommunityCalendarEvent))
        assert_that(new_io, has_properties({'title': 'reading',
                                            'description': 'this is',
                                            'location': 'oklahoma',
                                            'start_time': not_none(),
                                            'end_time': not_none(),
                                            'icon': '/abc/efg',
                                            'lastModified': not_none()}))

    def testUserCalendar(self):
        obj = UserCalendar(title=u"today", description=u'let us go')
        external = toExternalObject(obj)
        assert_that(external, has_entries({'Class': 'UserCalendar',
                                           'title': 'today',
                                           'description': 'let us go',
                                           "MimeType": "application/vnd.nextthought.calendar.usercalendar"}))

        external = {'title': u'future', 'description': 'do not go'}
        new_obj = self._internalize(external, obj, factory_=None)
        assert_that(new_obj, same_instance(obj))
        assert_that(new_obj, has_properties({'title': 'future', 'description': 'do not go'}))

        assert_that(self._internalize(external, factory_=None), is_(None))

    def testCommunityCalendar(self):
        obj = CommunityCalendar(title=u"today", description=u'let us go')
        external = toExternalObject(obj)
        assert_that(external, has_entries({'Class': 'CommunityCalendar',
                                           'title': 'today',
                                           'description': 'let us go',
                                           "MimeType": "application/vnd.nextthought.calendar.communitycalendar"}))

        external = {'title': u'future', 'description': 'do not go'}
        new_obj = self._internalize(external, obj, factory_=None)
        assert_that(new_obj, same_instance(obj))
        assert_that(new_obj, has_properties({'title': 'future', 'description': 'do not go'}))

        assert_that(self._internalize(external, factory_=None), is_(None))
