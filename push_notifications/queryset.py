from django.db.models import query


class MessageQuerySet(query.QuerySet):

    def send_message(self, message, **kwargs):
        """Send a message to the device.

        Args:
            message: Contents of the message being sent.
            **kwargs: Additional parameters.
        """
        raise NotImplementedError(
            "The class {cls} should implement the methhod 'send_message'.".format(
                cls=self.__class__
            )
        )


class BareDeviceQuerySet(MessageQuerySet):

    def send_message(self, message, **kwargs):
        if not self:
            return

        gcm_devices = []
        apns_devices = []
        wns_devices = []

        for device in self:
            if device.service == self.model.APNS:
                apns_devices.append(device)
            elif device.service == self.model.GCM:
                gcm_devices.append(device)
            elif device.service == self.model.WNS:
                wns_devices.append(device)

        if apns_devices:
            from .apns import apns_send_bulk_message
            apns_send_bulk_message(
                devices=apns_devices,
                alert=message,
                certificate=apns_devices[0].APNS_CERTIFICATE,
                **kwargs
            )

        if gcm_devices:
            data = kwargs.pop("extra", {})
            if message is not None:
                data["message"] = message

            from .gcm import gcm_send_bulk_message
            gcm_send_bulk_message(
                devices=gcm_devices,
                data=data,
                api_key=gcm_devices[0].GCM_API_KEY,
                **kwargs
            )

        if wns_devices:
            registration_ids = [device.registration_id for device in wns_devices]

            from .wns import wns_send_bulk_message
            wns_send_bulk_message(
                uri_list=registration_ids,
                message=message,
                **kwargs
            )


class GCMDeviceQuerySet(MessageQuerySet):

    def send_message(self, message, **kwargs):
        if not self:
            return None

        from .gcm import send_message as gcm_send_message

        data = kwargs.pop("extra", {})
        if message is not None:
            data["message"] = message

        app_ids = self.filter(
            active=True
        ).values_list(
            "application_id",
            flat=True
        ).distinct()
        responses = []
        for cloud_type in ("FCM", "GCM"):
            for app_id in app_ids:
                reg_ids = list(
                    self.filter(
                        active=True,
                        cloud_message_type=cloud_type,
                        application_id=app_id
                    ).values_list(
                        "registration_id",
                        flat=True
                    )
                )
                if reg_ids:
                    response = gcm_send_message(
                        reg_ids,
                        data,
                        cloud_type,
                        application_id=app_id,
                        **kwargs
                    )
                    responses.append(response)

        return responses


class APNSDeviceQuerySet(MessageQuerySet):

    def send_message(self, message, certfile=None, **kwargs):
        if not self:
            return None

        from .apns import apns_send_bulk_message

        app_ids = self.filter(
            active=True
        ).values_list(
            "application_id",
            flat=True
        ).distinct()
        responses = []
        for app_id in app_ids:
            reg_ids = list(self.filter(
                active=True,
                application_id=app_id
            ).values_list(
                "registration_id",
                flat=True)
            )
            response = apns_send_bulk_message(
                registration_ids=reg_ids,
                alert=message,
                application_id=app_id,
                certfile=certfile,
                **kwargs
            )
            if hasattr(response, "keys"):
                responses += [response]
            elif hasattr(response, "__getitem__"):
                responses += response
        return responses


class WNSDeviceQuerySet(MessageQuerySet):

    def send_message(self, message, **kwargs):
        if not self:
            return None

        from .wns import wns_send_bulk_message

        app_ids = self.filter(
            active=True
        ).values_list(
            "application_id",
            flat=True
        ).distinct()
        responses = []
        for app_id in app_ids:
            reg_ids = list(
                self.filter(
                    active=True,
                    application_id=app_id
                ).values_list(
                    "registration_id", flat=True
                )
            )
            response = wns_send_bulk_message(
                uri_list=reg_ids,
                message=message,
                **kwargs
            )
            if hasattr(response, "keys"):
                responses += [response]
            elif hasattr(response, "__getitem__"):
                responses += response
        return responses
