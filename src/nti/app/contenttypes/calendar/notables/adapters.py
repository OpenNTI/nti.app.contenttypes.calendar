from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.app.pushnotifications.interfaces import INotableDataEmailClassifier

from nti.contenttypes.calendar.interfaces import ICalendarEvent

from nti.externalization.singleton import Singleton


@component.adapter(ICalendarEvent)
@interface.implementer(INotableDataEmailClassifier)
class _CalendarEventNotableClassifier(Singleton):

    classification = 'calendar_event'

    def classify(self, unused_obj):
        return self.classification
