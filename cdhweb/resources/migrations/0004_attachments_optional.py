# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2018-03-09 16:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0003_attachment_pages'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='pages',
            field=models.ManyToManyField(blank=True, related_name='attachments', to='pages.Page'),
        ),
    ]
