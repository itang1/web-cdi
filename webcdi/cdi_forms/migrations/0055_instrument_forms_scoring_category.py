# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-24 11:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0054_choices_choice_set_en_ca_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument_forms',
            name='scoring_category',
            field=models.CharField(blank=True, max_length=101, null=True),
        ),
    ]