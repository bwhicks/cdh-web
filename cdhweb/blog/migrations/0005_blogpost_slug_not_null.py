# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-08 19:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_blogpost_is_featured'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpost',
            name='slug',
            field=models.CharField(blank=True, help_text='Leave blank to have the URL auto-generated from the title.', max_length=2000, verbose_name='URL'),
        ),
    ]
