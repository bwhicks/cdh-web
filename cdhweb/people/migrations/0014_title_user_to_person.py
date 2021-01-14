# Generated by Django 2.2.17 on 2020-12-23 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0013_position_user_to_person'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='position',
            name='user',
        ),
        migrations.AlterField(
            model_name='title',
            name='positions',
            field=models.ManyToManyField(through='people.Position', to='people.Person'),
        ),
        # revert field to non-nullable after it is populated
        migrations.AlterField(
            model_name='position',
            name='person',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='people.Person'),
        ),
    ]