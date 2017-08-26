from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from .apns import (apns_fetch_inactive_ids, apns_send_bulk_message,
                   apns_send_message)
from .fields import HexIntegerField


class DeviceManager(models.Manager):

	def get_queryset(self):
		return DeviceQuerySet(self.model)

	def invalidate(self, registration_ids):
		"""Called when some registration ids are deemed invalid. """
		self.filter(registration_id__in=registration_ids).update(service=self.model.INACTIVE)


class DeviceQuerySet(models.query.QuerySet):
	def send_message(self, message, **kwargs):
		if self:
			gcmDevices = []
			apnsDevices = []

			for device in self:
				if device.service == self.model.APNS:
					apnsDevices.append(device)
				elif device.service == self.model.GCM:
					gcmDevices.append(device)

			if apnsDevices:
				apns_send_bulk_message(
					devices=apnsDevices,
					alert=message,
					certificate=apnsDevices[0].APNS_CERTIFICATE,
					**kwargs
				)

			if gcmDevices:
				data = kwargs.pop("extra", {})
				if message is not None:
					data["message"] = message

				from .gcm import gcm_send_bulk_message
				return gcm_send_bulk_message(
					devices=gcmDevices,
					data=data,
					api_key=gcmDevices[0].GCM_API_KEY,
					**kwargs
				)
			return None


class BareDevice(models.Model):

	GCM = 0
	APNS = 1
	INACTIVE = 2

	SERVICES = (
		(GCM, "GCM"),
		(APNS, "APNS"),
		(INACTIVE, "Inactive"),
	)

	service = models.IntegerField(
		choices=SERVICES,
		verbose_name=_("Notification service"),
		default=INACTIVE
	)
	registration_id = models.TextField(
		blank=True,
		verbose_name=_("Registration ID")
	)

	objects = DeviceManager()
	APNS_CERTIFICATE = settings.PUSH_NOTIFICATIONS_SETTINGS.get("APNS_CERTIFICATE", None) if hasattr(settings, 'PUSH_NOTIFICATIONS_SETTINGS') else None
	GCM_API_KEY = settings.PUSH_NOTIFICATIONS_SETTINGS.get("GCM_API_KEY", None) if hasattr(settings, 'PUSH_NOTIFICATIONS_SETTINGS') else None

	class Meta:
		abstract = True

	@cached_property
	def active(self):
		return self.service != self.INACTIVE

	def save(self, *args, **kwargs):
		if (self.service != self.INACTIVE and not self.registration_id):
			self.invalidate(save=False)
		if (self.service == self.APNS and len(self.registration_id) > 64):
			raise ValidationError("APNS registration_id's max length is 64.")
		super(BareDevice, self).save(*args, **kwargs)

	def send_message(self, message, **kwargs):
		if self.active:
			if self.service == self.APNS:
				return apns_send_message(
					device=self,
					alert=message,
					certificate=self.APNS_CERTIFICATE,
					**kwargs
				)
			else:
				data = kwargs.pop("extra", {})
				if message is not None:
					data["message"] = message
				from .gcm import gcm_send_message
				return gcm_send_message(
					device=self,
					data=data,
					api_key=self.GCM_API_KEY,
					**kwargs
				)

	def invalidate(self, save=True):
		""" Called when the registration_id is deemed invalid. """
		self.service = self.INACTIVE
		if save:
			self.save()

	def __unicode__(self):
		return "{service}: {registration_id}".format(
			service=self.get_service_display(),
			registration_id=self.registration_id
		)


class Device(models.Model):
	name = models.CharField(max_length=255, verbose_name=_("Name"), blank=True, null=True)
	active = models.BooleanField(verbose_name=_("Is active"), default=True,
		help_text=_("Inactive devices will not be sent notifications"))
	user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
	date_created = models.DateTimeField(verbose_name=_("Creation date"), auto_now_add=True, null=True)

	class Meta:
		abstract = True

	def __unicode__(self):
		return self.name or \
			str(self.device_id or "") or \
			"%s for %s" % (self.__class__.__name__, self.user or "unknown user")


class GCMDeviceManager(models.Manager):
	def get_queryset(self):
		return GCMDeviceQuerySet(self.model)


class GCMDeviceQuerySet(models.query.QuerySet):
	def send_message(self, message, **kwargs):
		if self:
			from .gcm import gcm_send_bulk_message

			data = kwargs.pop("extra", {})
			if message is not None:
				data["message"] = message

			return gcm_send_bulk_message(devices=self, data=data, **kwargs)


class GCMDevice(Device):
	# device_id cannot be a reliable primary key as fragmentation between different devices
	# can make it turn out to be null and such:
	# http://android-developers.blogspot.co.uk/2011/03/identifying-app-installations.html
	device_id = HexIntegerField(verbose_name=_("Device ID"), blank=True, null=True, db_index=True,
		help_text=_("ANDROID_ID / TelephonyManager.getDeviceId() (always as hex)"))
	registration_id = models.TextField(verbose_name=_("Registration ID"))

	objects = GCMDeviceManager()

	class Meta:
		verbose_name = _("GCM device")

	def send_message(self, message, **kwargs):
		from .gcm import gcm_send_message
		data = kwargs.pop("extra", {})
		if message is not None:
			data["message"] = message
		return gcm_send_message(device=self, data=data, **kwargs)


class APNSDeviceManager(models.Manager):
	def get_queryset(self):
		return APNSDeviceQuerySet(self.model)


class APNSDeviceQuerySet(models.query.QuerySet):
	def send_message(self, message, **kwargs):
		if self:
			return apns_send_bulk_message(devices=self, alert=message, **kwargs)


class APNSDevice(Device):
	device_id = models.UUIDField(verbose_name=_("Device ID"), blank=True, null=True, db_index=True,
		help_text="UDID / UIDevice.identifierForVendor()")
	registration_id = models.CharField(verbose_name=_("Registration ID"), max_length=64, unique=True)

	objects = APNSDeviceManager()

	class Meta:
		verbose_name = _("APNS device")

	def send_message(self, message, **kwargs):
		return apns_send_message(device=self, alert=message, **kwargs)


# This is an APNS-only function right now, but maybe GCM will implement it
# in the future.  But the definition of 'expired' may not be the same. Whatevs
def get_expired_tokens():
	return apns_fetch_inactive_ids()
