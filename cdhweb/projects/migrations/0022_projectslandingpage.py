# Generated by Django 2.2.17 on 2021-01-15 14:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cdhpages', '0002_allow_body_h2'),
        ('projects', '0021_rename_mezz_project_fks'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectsLandingPage',
            fields=[
                ('landingpage_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='cdhpages.LandingPage')),
            ],
            options={
                'abstract': False,
            },
            bases=('cdhpages.landingpage',),
        ),
    ]
