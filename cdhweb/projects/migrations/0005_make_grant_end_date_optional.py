# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-16 20:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_project_cdh_built'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grant',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
