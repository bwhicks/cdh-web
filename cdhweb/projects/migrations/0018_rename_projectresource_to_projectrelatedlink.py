# Generated by Django 2.2.17 on 2021-01-14 16:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdhpages', '0002_relatedlinktype'),
        ('projects', '0017_update_to_relatedlinktype_field'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ProjectResource',
            new_name='ProjectRelatedLink',
        ),
    ]
