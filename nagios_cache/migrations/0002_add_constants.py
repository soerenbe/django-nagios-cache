# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-07-11 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nagios_cache', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nagioshoststatus',
            name='status',
            field=models.SmallIntegerField(choices=[[1, 'OK'], [2, 'UP'], [3, 'DOWN'], [4, 'WARNING'], [5, 'CRITICAL'], [6, 'UNKNOWN'], [7, 'PENDING'], [8, 'UNREACHABLE']]),
        ),
        migrations.AlterField(
            model_name='nagiosservicestatus',
            name='status',
            field=models.SmallIntegerField(choices=[[1, 'OK'], [2, 'UP'], [3, 'DOWN'], [4, 'WARNING'], [5, 'CRITICAL'], [6, 'UNKNOWN'], [7, 'PENDING'], [8, 'UNREACHABLE']]),
        ),
    ]

