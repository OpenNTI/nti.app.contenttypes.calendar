#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import calendar
import math
import time

from zope.cachedescriptors.property import Lazy

from nameparser import HumanName

from pyramid.request import Request

from pyramid.threadlocal import get_current_request
from pyramid.threadlocal import get_current_registry

from zope import component
from zope import interface

from nti.app.contenttypes import calendar as calendar_pkg
from nti.app.contenttypes.calendar.utils import generate_calendar_event_url

from nti.contenttypes.calendar.interfaces import ICalendarEventNotifier

from nti.dataserver.interfaces import IUser

from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.mailer.interfaces import IEmailAddressable
from nti.mailer.interfaces import ITemplatedMailer

logger = __import__('logging').getLogger(__name__)


def _mailer():
    return component.getUtility(ITemplatedMailer)


@interface.implementer(ICalendarEventNotifier)
class CalendarEventNotifier(object):

    template = u'calendar_event'

    text_template_extension = u'.mak'

    def __init__(self, calendar_event):
        self.context = calendar_event

    def _subject(self):
        return 'Upcoming calendar event'

    def _recipients(self):
        raise NotImplementedError

    def _calendar_context(self):
        raise NotImplementedError

    @Lazy
    def _remaining(self):
        start = calendar.timegm(self.context.start_time.utctimetuple())
        remaining = start - time.time()
        return int(math.ceil(remaining/60)) if remaining > 0 else None

    @Lazy
    def _event_start(self):
        return "Beginning in {0} minutes.".format(self._remaining)

    @Lazy
    def _event_url(self):
        # For testing.
        return generate_calendar_event_url(self.context)

    def _template_args(self, user, **kwargs):
        realname = IFriendlyNamed(user).realname
        template_args = {}
        template_args.update({
            'first_name': HumanName(realname).first if realname else IEmailAddressable(user).email,
            'event_title': self.context.title,
            'event_description': self.context.description,
            'event_start': self._event_start,
            'event_location': self.context.location,
            'event_url': kwargs.get('event_url', None) or self._event_url,
            'event_remaining': self._remaining
        })
        return template_args

    def _calendar_pkg(self):
        return calendar_pkg

    @Lazy
    def _request(self):
        request = get_current_request()
        if request is None:
            # fake a request
            request = Request({})
            request.context = self.context
            request.registry = get_current_registry()
        return request

    def _do_send(self, mailer, *args, **kwargs):
        # do not send if the event has started?
        if self._remaining is None:
            logger.warning("Ignoring the notification of started calendar event (title=%s, start_time=%s).",
                           self.context.title, self.context.start_time)
            return

        for user in self._recipients() or ():
            if not IUser.providedBy(user):
                continue

            addr = IEmailAddressable(user, None)
            if not addr or not addr.email:
                continue

            # Info level for now
            logger.info('Emailing calendar notification (%s) (%s) (%s)',
                        user.username,
                        addr.email,
                        self.context.title)
            mailer.queue_simple_html_text_email(self.template,
                                                subject=self._subject(),
                                                recipients=[addr.email],
                                                template_args=self._template_args(user, **kwargs),
                                                reply_to=None,
                                                package=self._calendar_pkg(),
                                                request=self._request,
                                                text_template_extension=self.text_template_extension)

    def notify(self, *args, **kwargs):
        mailer = _mailer()
        self._do_send(mailer, *args, **kwargs)
