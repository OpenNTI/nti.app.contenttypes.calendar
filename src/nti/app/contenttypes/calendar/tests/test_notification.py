#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

import fudge
import time

from datetime import datetime

from hamcrest import is_
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import not_none
from hamcrest import has_entries
from hamcrest import has_properties

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.app.contenttypes import calendar as calendar_pkg

from nti.app.contenttypes.calendar.notification import CalendarEventNotifier

from nti.contenttypes.calendar.model import CalendarEvent

from nti.dataserver.tests import mock_dataserver as mock_dataserver
from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import User
from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.mailer.interfaces import IEmailAddressable


class TestNotification(ApplicationLayerTest):

    @WithMockDSTrans
    @fudge.patch('nti.app.contenttypes.calendar.notification._mailer')
    def testCalendarEventNotifier(self, mock_mailer):
        user1 = User.create_user(username=u'test001')
        user2 = User.create_user(username=u'test002')
        class _MockEventNotifier(CalendarEventNotifier):
            def _calendar_context(self):
                return u'Course'
            def _recipients(self):
                return [user1, u'abc', user2, None]

        class _MockItem(object):
            def __init__(self, template, subject, recipients, template_args, reply_to, package, request, text_template_extension):
                self.template = template
                self.subject = subject
                self.recipients = recipients
                self.template_args = template_args
                self.reply_to = reply_to
                self.package = package
                self.request = request
                self.text_template_extension = text_template_extension

        class _MockMailer(object):
            def __init__(self):
                self.data = []

            def queue_simple_html_text_email(self, *args, **kwargs):
                item = _MockItem(*args, **kwargs)
                self.data.append(item)

            def clear(self):
                self.data[:] = []

        _mailer = _MockMailer()
        assert_that(_mailer.data, has_length(0))
        mock_mailer.is_callable().returns(_mailer)

        event = CalendarEvent(title=u'abc')
        notifier = _MockEventNotifier(event)
        notifier._remaining = 25
        notifier.notify()
        assert_that(_mailer.data, has_length(0))

        addr = IEmailAddressable(user1, None)
        addr.email = u'abc@example.com'
        notifier.notify()
        assert_that(_mailer.data, has_length(1))

        _mailer.clear()
        addr = IEmailAddressable(user2, None)
        addr.email = u'abc2@example.com'

        notifier.notify()
        assert_that(_mailer.data, has_length(2))
        assert_that(_mailer.data[0], has_properties({'template': 'calendar_event',
                                                                 'subject': 'Upcoming calendar event',
                                                                 'recipients': has_length(1),
                                                                 'template_args': has_entries({'first_name': 'abc@example.com'}),
                                                                 'reply_to': None,
                                                                 'package': calendar_pkg,
                                                                 'request': not_none(),
                                                                 'text_template_extension': '.mak'}))
        assert_that(_mailer.data[0].recipients[0], is_('abc@example.com'))

        assert_that(_mailer.data[1], has_properties({'template': 'calendar_event',
                                                                 'subject': 'Upcoming calendar event',
                                                                 'recipients': has_length(1),
                                                                 'template_args': has_entries({'first_name': 'abc2@example.com'}),
                                                                 'reply_to': None,
                                                                 'package': calendar_pkg,
                                                                 'request': not_none(),
                                                                 'text_template_extension': '.mak'}))
        assert_that(_mailer.data[1].recipients[0], is_('abc2@example.com'))