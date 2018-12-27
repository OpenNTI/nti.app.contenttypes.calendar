#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import


from zope import interface

from zope.location.interfaces import IContained


@interface.implementer(IContained)
class PluginPoint(object):

    __parent__ = None

    def __init__(self, name):
        self.__name__ = name
PP_CALENDAR = PluginPoint('nti.contenttypes.calendar')