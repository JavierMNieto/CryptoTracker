# Generated by Django 2.1.5 on 2019-02-10 03:44

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usdt', '0007_auto_20190206_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='minTx',
            field=models.FloatField(default=1000000.0),
        ),
        migrations.AlterField(
            model_name='node',
            name='tx_Since',
            field=models.DateField(default=datetime.date(2018, 2, 9)),
        ),
    ]