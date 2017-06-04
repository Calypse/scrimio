# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-04 05:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mm_base', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='party',
            name='expedited_fairness',
            field=models.IntegerField(default=0.45),
        ),
        migrations.AddField(
            model_name='party',
            name='is_expedited',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='party',
            name='region',
            field=models.CharField(blank=True, choices=[(None, 'Choose Region'), ('USW', 'US West'), ('USE', 'US East'), ('EUW', 'EU West'), ('EUC', 'EU Central'), ('EUE', 'EU East')], default=None, max_length=4),
        ),
    ]