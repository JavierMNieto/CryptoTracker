# Generated by Django 2.1.5 on 2019-02-18 16:48

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usdt', '0008_auto_20190209_2144'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='category',
            field=models.CharField(default='', max_length=36, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='node',
            name='USDT_Address',
            field=models.CharField(max_length=250, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='node',
            name='name',
            field=models.CharField(max_length=250, validators=[django.core.validators.RegexValidator('^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')]),
        ),
        migrations.AlterField(
            model_name='node',
            name='tx_Since',
            field=models.DateField(default=datetime.date(2018, 2, 18)),
        ),
    ]