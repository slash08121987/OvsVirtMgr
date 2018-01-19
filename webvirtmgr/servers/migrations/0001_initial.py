# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-29 07:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Compute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('hostname', models.CharField(max_length=20)),
                ('login', models.CharField(max_length=20)),
                ('password', models.CharField(blank=True, max_length=14, null=True)),
                ('type', models.IntegerField()),
            ],
        ),
    ]
