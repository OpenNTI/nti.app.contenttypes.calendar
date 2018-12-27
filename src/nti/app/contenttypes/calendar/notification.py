#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nameparser import HumanName

from pyramid.request import Request

from pyramid.threadlocal import get_current_request
from pyramid.threadlocal import get_current_registry

from zope import component
from zope import interface

from nti.app.contenttypes import calendar as calendar_pkg

from nti.contenttypes.calendar.interfaces import ICalendarEventNotifier

from nti.dataserver.interfaces import IUser

from nti.dataserver.users import User
from nti.dataserver.users.interfaces import IFriendlyNamed

from nti.mailer.interfaces import IEmailAddressable
from nti.mailer.interfaces import ITemplatedMailer
from nti.mailer.interfaces import EmailAddresablePrincipal


def _mailer():
    return component.getUtility(ITemplatedMailer)


@interface.implementer(ICalendarEventNotifier)
class CalendarEventNotifier(object):

    template = u'calendar_event'

    text_template_extension = u'.mak'

    def __init__(self, calendar_event):
        self.context = calendar_event

    def _subject(self):
        return u'Upcoming calendar event'

    def _recipients(self):
        raise NotImplementedError

    def _template_args(self, user, **kwargs):
        realname = IFriendlyNamed(user).realname
        template_args = {
            'first_name': HumanName(realname).first if realname else IEmailAddressable(user).email,
        }
        template_args.update(kwargs)
        return template_args

    def _calendar_pkg(self):
        return calendar_pkg

    def _request(self):
        request = get_current_request()
        if request is None:
            # fake a request
            request = Request({})
            request.context = self.context
            request.registry = get_current_registry()
        return request

    def _do_send(self, mailer, *args, **kwargs):
        for user in self._recipients() or ():
            if not IUser.providedBy(user):
                continue

            addr = IEmailAddressable(user, None)
            if not addr or not addr.email:
                continue

            mailer.queue_simple_html_text_email(self.template,
                                                subject=self._subject(),
                                                recipients=[addr.email],
                                                template_args=self._template_args(user, **kwargs),
                                                reply_to=None,
                                                package=self._calendar_pkg(),
                                                request=self._request(),
                                                text_template_extension=self.text_template_extension)

    def notify(self, *args, **kwargs):
        mailer = _mailer()
        self._do_send(mailer, *args, **kwargs)
