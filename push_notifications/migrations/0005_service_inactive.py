# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0004_simpledevice_registration_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='simpledevice',
            name='active',
        ),
        migrations.AlterField(
            model_name='simpledevice',
            name='service',
            field=models.IntegerField(default=2, verbose_name='Notification service', choices=[(0, 'GCM'), (1, 'APNS'), (2, 'Inactive')]),
        ),
    ]
