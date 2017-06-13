from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from .fields import HexIntegerField
from .managers import (APNSDeviceManager, BareDeviceManager, GCMDeviceManager,
                       WNSDeviceManager)
from .settings import PUSH_NOTIFICATIONS_SETTINGS as SETTINGS

CLOUD_MESSAGE_TYPES = (
    ("FCM", "Firebase Cloud Message"),
    ("GCM", "Google Cloud Message"),
)


@python_2_unicode_compatible
class Device(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        blank=True,
        null=True
    )
    active = models.BooleanField(
        verbose_name=_("Is active"),
        default=True,
        help_text=_("Inactive devices will not be sent notifications")
    )
    user = models.ForeignKey(
        SETTINGS["USER_MODEL"],
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    date_created = models.DateTimeField(
        verbose_name=_("Creation date"),
        auto_now_add=True,
        null=True
    )
    application_id = models.CharField(
        max_length=64,
        verbose_name=_("Application ID"),
        help_text=_(
            "Opaque application identity, should be filled in for multiple "
            "key/certificate access"
        ),
        blank=True,
        null=True
    )

    class Meta:
        abstract = True

    def __str__(self):
        return (
            self.name or
            str(self.device_id or "") or
            "{cls} for {user}".format(
                cls=self.__class__.__name__,
                user=self.user or "unknown user"
            )
        )


class BareDevice(models.Model):

    GCM = 0
    APNS = 1
    INACTIVE = 2
    FCM = 3
    WNS = 4
    SERVICES = (
        (GCM, "GCM"),
        (APNS, "APNS"),
        (INACTIVE, "Inactive"),
        (FCM, "FCM"),
        (WNS, "WNS"),
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

    objects = BareDeviceManager()

    APNS_CERTIFICATE = SETTINGS.get("APNS_CERTIFICATE", None)
    GCM_API_KEY = SETTINGS.get("GCM_API_KEY", None)
    WNS_CLIENT_ID = SETTINGS.get("WNS_PACKAGE_SECURITY_ID", None)
    WNS_CLIENT_SECRET = SETTINGS.get("WNS_SECRET_KEY", None)

    class Meta:
        abstract = True

    @cached_property
    def active(self):
        return self.service != self.INACTIVE

    def save(self, *args, **kwargs):
        if self.service != self.INACTIVE and not self.registration_id:
            self.invalidate(save=False)
        if self.service == self.APNS and len(self.registration_id) > 64:
            raise ValidationError("APNS registration_id's max length is 64.")
        super(BareDevice, self).save(*args, **kwargs)

    def send_message(self, message, apns_certificate=None, **kwargs):
        if apns_certificate is None:
            apns_certificate = self.APNS_CERTIFICATE

        if self.active:
            if self.service == self.APNS:
                from .apns import apns_send_message

                return apns_send_message(
                    registration_id=self.registration_id,
                    alert=message,
                    certfile=apns_certificate,
                    **kwargs
                )
            elif self.service == self.WNS:
                from .wns import wns_send_message

                return wns_send_message(
                    uri=self.registration_id,
                    message=message,
                    client_id=self.WNS_CLIENT_ID,
                    client_secret=self.WNS_CLIENT_SECRET,
                    **kwargs
                )
            else:
                data = kwargs.pop("extra", {})
                if message is not None:
                    data["message"] = message
                from .gcm import send_message as gcm_send_message
                return gcm_send_message(
                    device=self,
                    data=data,
                    api_key=self.GCM_API_KEY,
                    **kwargs
                )
                cloud_types = {
                    self.GCM: "GCM",
                    self.FCM: "FCM",
                }
                return gcm_send_message(
                    registration_ids=[self.registration_id],
                    data=data,
                    cloud_type=cloud_types[self.service],
                    application_id=self.application_id,
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


class GCMDevice(Device):
    # device_id cannot be a reliable primary key as fragmentation between different devices
    # can make it turn out to be null and such:
    # http://android-developers.blogspot.co.uk/2011/03/identifying-app-installations.html
    device_id = HexIntegerField(
        verbose_name=_("Device ID"),
        blank=True,
        null=True,
        db_index=True,
        help_text=_("ANDROID_ID / TelephonyManager.getDeviceId() (always as hex)")
    )
    registration_id = models.TextField(
        verbose_name=_("Registration ID")
    )
    cloud_message_type = models.CharField(
        verbose_name=_("Cloud Message Type"),
        max_length=3,
        choices=CLOUD_MESSAGE_TYPES,
        default="GCM",
        help_text=_("You should choose FCM or GCM")
    )
    objects = GCMDeviceManager()

    class Meta:
        verbose_name = _("GCM device")

    def send_message(self, message, **kwargs):
        from .gcm import send_message as gcm_send_message

        data = kwargs.pop("extra", {})
        if message is not None:
            data["message"] = message

        return gcm_send_message(
            self.registration_id,
            data,
            self.cloud_message_type,
            application_id=self.application_id,
            **kwargs
        )


class APNSDevice(Device):
    device_id = models.UUIDField(
        verbose_name=_("Device ID"),
        blank=True,
        null=True,
        db_index=True,
        help_text="UDID / UIDevice.identifierForVendor()"
    )
    registration_id = models.CharField(
        verbose_name=_("Registration ID"),
        max_length=200,
        unique=True
    )

    objects = APNSDeviceManager()

    class Meta:
        verbose_name = _("APNS device")

    def send_message(self, message, certfile=None, **kwargs):
        from .apns import apns_send_message

        return apns_send_message(
            registration_id=self.registration_id,
            alert=message,
            application_id=self.application_id,
            certfile=certfile,
            **kwargs
        )


class WNSDevice(Device):
    device_id = models.UUIDField(
        verbose_name=_("Device ID"),
        blank=True,
        null=True,
        db_index=True,
        help_text=_("GUID()")
    )
    registration_id = models.TextField(
        verbose_name=_("Notification URI")
    )

    objects = WNSDeviceManager()

    class Meta:
        verbose_name = _("WNS device")

    def send_message(self, message, **kwargs):
        from .wns import wns_send_message

        return wns_send_message(
            uri=self.registration_id,
            message=message,
            application_id=self.application_id,
            **kwargs
        )


SERVICE_INACTIVE = BareDevice.INACTIVE
