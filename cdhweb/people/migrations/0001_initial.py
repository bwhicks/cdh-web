# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-07 21:10
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import mezzanine.core.fields
import mezzanine.utils.models
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('auth', '0008_alter_user_username_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keywords_string', models.CharField(blank=True, editable=False, max_length=500)),
                ('title', models.CharField(max_length=500, verbose_name='Title')),
                ('slug', models.CharField(blank=True, help_text='Leave blank to have the URL auto-generated from the title.', max_length=2000, null=True, verbose_name='URL')),
                ('_meta_title', models.CharField(blank=True, help_text='Optional title to be used in the HTML title tag. If left blank, the main title field will be used.', max_length=500, null=True, verbose_name='Title')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('gen_description', models.BooleanField(default=True, help_text='If checked, the description will be automatically generated from content. Uncheck if you want to manually set a custom description.', verbose_name='Generate description')),
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('status', models.IntegerField(choices=[(1, 'Draft'), (2, 'Published')], default=2, help_text='With Draft chosen, will only be shown for admin users on the site.', verbose_name='Status')),
                ('publish_date', models.DateTimeField(blank=True, db_index=True, help_text="With Published chosen, won't be shown until this time", null=True, verbose_name='Published from')),
                ('expiry_date', models.DateTimeField(blank=True, help_text="With Published chosen, won't be shown after this time", null=True, verbose_name='Expires on')),
                ('short_url', models.URLField(blank=True, null=True)),
                ('in_sitemap', models.BooleanField(default=True, verbose_name='Show in sitemap')),
                ('education', mezzanine.core.fields.RichTextField()),
                ('bio', mezzanine.core.fields.RichTextField()),
                ('phone_number', models.CharField(blank=True, max_length=50)),
                ('office_location', models.CharField(blank=True, max_length=255)),
                ('image', mezzanine.core.fields.FileField(blank=True, max_length=255, null=True, verbose_name='Image')),
                ('thumb', mezzanine.core.fields.FileField(blank=True, max_length=255, null=True, verbose_name='Thumbnail')),
                ('site', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='sites.Site')),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, mezzanine.utils.models.AdminThumbMixin),
        ),
        migrations.CreateModel(
            name='Title',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
            ],
            options={
                'verbose_name_plural': 'People',
                'proxy': True,
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='title',
            name='positions',
            field=models.ManyToManyField(related_name='titles', through='people.Position', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='position',
            name='title',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.Title'),
        ),
        migrations.AddField(
            model_name='position',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='positions', to=settings.AUTH_USER_MODEL),
        ),
    ]
