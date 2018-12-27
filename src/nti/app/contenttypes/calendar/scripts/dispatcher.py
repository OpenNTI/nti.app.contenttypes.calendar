#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from z3c.autoinclude.zcml import includePluginsDirective

from nti.app.asynchronous.processor import Processor

from nti.app.contenttypes.calendar.scripts import PP_CALENDAR

from nti.contenttypes.calendar import SCHEDULED_QUEUE_NAMES

class Constructor(Processor):

    def extend_context(self, context):
        includePluginsDirective(context, PP_CALENDAR)

    def process_args(self, args):
        setattr(args, 'redis', True)
        setattr(args, 'scheduled', True)
        setattr(args, 'queue_names', SCHEDULED_QUEUE_NAMES)
        super(Constructor, self).process_args(args)


def main():
    return Constructor()()


if __name__ == '__main__':
    main()
