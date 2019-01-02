#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

logger = __import__('logging').getLogger(__name__)

from zope import component

from pyramid.view import view_config

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.contenttypes.calendar.utils import CALENDAR_TOKEN_SCOPE

from nti.dataserver import authorization as nauth

from nti.dataserver.interfaces import IUser
from nti.dataserver.interfaces import IDataserver
from nti.dataserver.interfaces import IShardLayout
from nti.dataserver.interfaces import IDataserverFolder

from nti.dataserver.users.interfaces import IUserTokenContainer

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL


@view_config(route_name='objects.generic.traversal',
             name='ResetCalendarTokens',
             renderer='rest',
             request_method='POST',
             permission=nauth.ACT_NTI_ADMIN,
             context=IDataserverFolder)
class UserCalendarResetView(AbstractAuthenticatedView):
    """
    This should be a one-time alpha (and dev) view to reset calendar tokens.
    A general token management API is preferred and should be available soon.
    """

    def __call__(self):
        result = LocatedExternalDict()

        dataserver = component.getUtility(IDataserver)
        users_folder = IShardLayout(dataserver).users_folder

        # This is pretty slow.
        for user in list(users_folder.values()):
            if not IUser.providedBy(user):
                continue

            token_container = IUserTokenContainer(user)
            calendar_tokens = token_container.get_all_tokens_by_scope(CALENDAR_TOKEN_SCOPE)
            for token in calendar_tokens or ():
                token_container.remove_token(token)
                logger.info("Removing calendar token (%s) (%s)",
                            user.username,
                            token.token)
                tokens = result.setdefault(user.username, [])
                tokens.append(token.token)
        return result
