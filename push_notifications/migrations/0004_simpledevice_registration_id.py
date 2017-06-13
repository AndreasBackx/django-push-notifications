# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('push_notifications', '0003_baredevice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='simpledevice',
            name='registration_id',
            field=models.TextField(verbose_name='Registration ID', blank=True),
        ),
    ]
