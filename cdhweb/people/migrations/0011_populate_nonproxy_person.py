# Generated by Django 2.2.17 on 2020-12-22 16:54

from django.conf import settings
from django.db import migrations


def create_nonproxy_persons(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Person = apps.get_model('people', 'Person')

    # iterate over all users (except script user) and create person records
    # populate new person from user and profile
    # set user - person 1:1 and save
    for user in User.objects.exclude(username=settings.SCRIPT_USERNAME):
        person_info = {
            'user': user,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        # get profile if there is one (not all users have them)
        profile = getattr(user, 'profile', None)
        if profile:
            person_info.update({
                'cdh_staff': profile.is_staff,
                'job_title': profile.job_title,
                'department': profile.department,
                'institution': profile.institution,
                'pu_status': user.profile.pu_status
            })
        Person.objects.create(**person_info)

    # TODO: do we care about log entries for person creation?
    # get script user and log entry model to document changes
    # script_user = User.objects.get(username=settings.SCRIPT_USERNAME)
    # LogEntry = apps.get_model('admin', 'LogEntry')
    # ContentType = apps.get_model('contenttypes', 'ContentType')


def remove_nonproxy_persons(apps, schema_editor):
    Person = apps.get_model('people', 'Person')
    Person.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0010_nonproxy_person'),
    ]

    operations = [
        migrations.RunPython(create_nonproxy_persons,
                             reverse_code=remove_nonproxy_persons)
    ]
