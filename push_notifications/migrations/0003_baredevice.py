# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0002_newdevice'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimpleDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('service', models.IntegerField(verbose_name='Notification service', choices=[(0, b'GCM'), (1, b'APNS')])),
                ('registration_id', models.TextField(verbose_name='Registration ID')),
                ('active', models.BooleanField(default=True, help_text='Inactive devices will not be sent notifications', verbose_name='Is active')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='NewDevice',
        ),
    ]
