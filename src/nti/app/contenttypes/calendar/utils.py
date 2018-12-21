#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

from datetime import datetime
from datetime import timedelta

from six.moves import urllib_parse

from zope import component
from zope import interface

from nti.app.contenttypes.calendar import CALENDARS

from nti.appserver.interfaces import IUserViewTokenCreator

from nti.dataserver.users.interfaces import IUserTokenContainer

from nti.dataserver.users.tokens import UserToken

from nti.links.externalization import render_link

from nti.links.interfaces import ILinkExternalHrefOnly

from nti.links.links import Link

CALENDAR_TOKEN_SCOPE = u"calendar:feed"


def generate_ics_feed_url(user, request):
    """
    Generates and returns a calendar feed url.
    """
    token_creator = component.queryUtility(IUserViewTokenCreator,
                                           name='calendar_feed.ics')
    token = token_creator.getTokenForUserId(user.username,
                                            CALENDAR_TOKEN_SCOPE)
    if not token:
        # Currently, we'll implicitly create the token for the user
        # By default, expire in one year
        token_container = IUserTokenContainer(user)
        one_year_later = datetime.utcnow() + timedelta(days=365)
        user_token = UserToken(title=u"Calendar feed token",
                               description=u"auto-generated feed token",
                               scopes=(CALENDAR_TOKEN_SCOPE,),
                               expiration_date=one_year_later)
        token_container.store_token(user_token)
        token = token_creator.getTokenForUserId(user.username,
                                                CALENDAR_TOKEN_SCOPE)
        request.environ['nti.request_had_transaction_side_effects'] = True
    link = Link(user,
                rel='feed',
                elements=(CALENDARS,
                          '@@calendar_feed.ics',),
                params={'token': token})
    interface.alsoProvides(link, ILinkExternalHrefOnly)
    feed_url = render_link(link)
    return urllib_parse.urljoin(request.application_url, feed_url)
