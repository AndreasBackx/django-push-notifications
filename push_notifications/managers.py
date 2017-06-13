from django.db import models

from .queryset import (APNSDeviceQuerySet, BareDeviceQuerySet,
                       GCMDeviceQuerySet, WNSDeviceQuerySet)


class BareDeviceManager(models.Manager):

    def get_queryset(self):
        return BareDeviceQuerySet(self.model)

    def invalidate(self, registration_ids):
        """ Called when some registration ids are deemed invalid. """
        self.filter(
            registration_id__in=registration_ids
        ).update(
            service=self.model.INACTIVE
        )


class GCMDeviceManager(models.Manager):

    def get_queryset(self):
        return GCMDeviceQuerySet(self.model)


class APNSDeviceManager(models.Manager):

    def get_queryset(self):
        return APNSDeviceQuerySet(self.model)


class WNSDeviceManager(models.Manager):

    def get_queryset(self):
        return WNSDeviceQuerySet(self.model)
