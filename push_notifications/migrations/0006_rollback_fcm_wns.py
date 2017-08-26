# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-26 13:07
from __future__ import unicode_literals

from django.db import migrations, models
import push_notifications.fields


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0005_service_inactive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apnsdevice',
            name='device_id',
            field=models.UUIDField(blank=True, db_index=True, help_text='UDID / UIDevice.identifierForVendor()', null=True, verbose_name='Device ID'),
        ),
        migrations.AlterField(
            model_name='gcmdevice',
            name='device_id',
            field=push_notifications.fields.HexIntegerField(blank=True, db_index=True, help_text='ANDROID_ID / TelephonyManager.getDeviceId() (always as hex)', null=True, verbose_name='Device ID'),
        ),
    ]