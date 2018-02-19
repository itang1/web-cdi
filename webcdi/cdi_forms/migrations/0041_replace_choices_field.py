# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-02-19 05:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0040_populate_choice_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='english_wg',
            name='choices',
        ),
        migrations.RemoveField(
            model_name='english_ws',
            name='choices',
        ),
        migrations.RemoveField(
            model_name='spanish_wg',
            name='choices',
        ),
        migrations.RemoveField(
            model_name='spanish_ws',
            name='choices',
        ),
        migrations.RenameField(
            model_name='english_wg',
            old_name='choices_link',
            new_name='choices'
        ),
        migrations.RenameField(
            model_name='english_ws',
            old_name='choices_link',
            new_name='choices'
        ),
        migrations.RenameField(
            model_name='spanish_wg',
            old_name='choices_link',
            new_name='choices'
        ),
        migrations.RenameField(
            model_name='spanish_ws',
            old_name='choices_link',
            new_name='choices'
        ),
    ]
