from django.db import models

from .queryset import APNSDeviceQuerySet, GCMDeviceQuerySet, WNSDeviceQuerySet


class GCMDeviceManager(models.Manager):

    def get_queryset(self):
        return GCMDeviceQuerySet(self.model)


class APNSDeviceManager(models.Manager):

    def get_queryset(self):
        return APNSDeviceQuerySet(self.model)


class WNSDeviceManager(models.Manager):

    def get_queryset(self):
        return WNSDeviceQuerySet(self.model)
